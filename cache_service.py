import time
import json
import hashlib
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple

# Suppress noisy Google GenAI SDK Automatic Function Calling (AFC) advisory warning
try:
    from google.genai import models as _google_genai_models
    _google_genai_models.Models._logged_afc_warning = True
except Exception:
    pass
logging.getLogger("google_genai").setLevel(logging.ERROR)
logging.getLogger("google.genai").setLevel(logging.ERROR)

import redis
import numpy as np
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from config import config

logger = logging.getLogger(__name__)

SUPPORT_SYSTEM_PROMPT = """You are an AI Support Concierge for 'CloudNova', a cloud SaaS company.
Provide helpful, professional, and concise answers to customer inquiries about subscriptions, billing, authentication, and platform features.
Keep responses concise, clear, and easy to read with markdown bullet points where appropriate."""


@dataclass
class QueryResult:
    answer: str
    is_cache_hit: bool
    latency_ms: float
    distance: Optional[float] = None
    similarity_pct: Optional[float] = None
    matched_prompt: Optional[str] = None
    hit_key: Optional[str] = None
    hit_count: Optional[int] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class CacheEntry:
    key: str
    prompt: str
    response: str
    ttl: Optional[int] = None


@dataclass
class LeaderboardEntry:
    rank: int
    key: str
    prompt: str
    hits: int
    response: Optional[str] = None


class SemanticCacheService:
    def __init__(self):
        self.config = config
        self.distance_threshold = config.distance_threshold
        self.ttl = config.cache_ttl
        self.index_name = f"{config.cache_index_name}:{config.cache_prefix}"
        self.prefix = f"{self.index_name}:"
        self.leaderboard_key = config.cache_leaderboard_key or f"{self.prefix}leaderboard"
        self.telemetry_key = config.cache_telemetry_key or f"{self.prefix}telemetry"
        self._raw_client: Optional[redis.Redis] = None
        self._text_client: Optional[redis.Redis] = None
        self._embeddings: Optional[GoogleGenerativeAIEmbeddings] = None
        self._llm: Optional[ChatGoogleGenerativeAI] = None
        self._index_initialized: bool = False

    def get_redis_client(self, decode_responses: bool = False) -> redis.Redis:
        """Get or initialize raw or text Redis/Valkey client."""
        url = self.config.get_redis_connection_url()
        is_ssl = url.startswith("rediss://") or self.config.valkey_ssl

        # NOTE: Disabling TLS certificate validation (ssl_cert_reqs=ssl.CERT_NONE and ssl_check_hostname=False)
        # allows connecting to self-signed or POC Valkey nodes over TLS without installing local CA certs.
        # WARNING: It is probably NOT best to disable TLS certificate verification in production environments.
        # In production, ensure valid CA-signed certificates and hostname verification are enforced.
        ssl_kwargs = {}
        if is_ssl:
            import ssl
            ssl_kwargs = {
                "ssl_cert_reqs": ssl.CERT_NONE,
                "ssl_check_hostname": False,
            }

        if decode_responses:
            if self._text_client is None:
                self._text_client = redis.Redis.from_url(
                    url,
                    decode_responses=True,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                    **ssl_kwargs,
                )
            return self._text_client
        else:
            if self._raw_client is None:
                self._raw_client = redis.Redis.from_url(
                    url,
                    decode_responses=False,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                    **ssl_kwargs,
                )
            return self._raw_client

    def ping_valkey(self) -> Tuple[bool, float, str]:
        """
        Ping the Valkey server to verify connectivity and measure latency.
        Returns:
            Tuple[bool, float, str]: (is_successful, latency_ms, message_or_error)
        """
        start = time.perf_counter()
        try:
            client = self.get_redis_client(decode_responses=True)
            pong = client.ping()
            latency_ms = (time.perf_counter() - start) * 1000.0
            if pong:
                return True, round(latency_ms, 2), "PONG"
            return False, round(latency_ms, 2), "No response from Valkey ping"
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000.0
            return False, round(latency_ms, 2), str(e)

    def test_valkey_connection(self) -> Tuple[bool, str]:
        """Test connection to remote Valkey server."""
        try:
            client = self.get_redis_client(decode_responses=True)
            client.ping()
            info = client.info("server")
            version = info.get("redis_version", info.get("valkey_version", "unknown"))
            host = client.connection_pool.connection_kwargs.get("host")
            port = client.connection_pool.connection_kwargs.get("port")
            return True, f"Connected to Valkey/Redis {version} at {host}:{port}"
        except Exception as e:
            return False, str(e)

    def test_vertex_connection(self) -> Tuple[bool, str]:
        """Test connection to Vertex AI."""
        try:
            emb = self.get_embeddings()
            vector = emb.embed_query("ping")
            return True, f"Vertex AI Ready ({self.config.vertex_model}, {self.config.vertex_embedding_model}, dim={len(vector)})"
        except Exception as e:
            return False, str(e)

    def get_embeddings(self) -> GoogleGenerativeAIEmbeddings:
        """Get or initialize GoogleGenerativeAIEmbeddings with Vertex AI."""
        if self._embeddings is None:
            self._embeddings = GoogleGenerativeAIEmbeddings(
                model=self.config.vertex_embedding_model,
                vertexai=True,
                project=self.config.gcp_project,
                location=self.config.gcp_location,
            )
        return self._embeddings

    def get_llm(self) -> ChatGoogleGenerativeAI:
        """Get or initialize ChatGoogleGenerativeAI with Vertex AI."""
        if self._llm is None:
            self._llm = ChatGoogleGenerativeAI(
                model=self.config.vertex_model,
                vertexai=True,
                project=self.config.gcp_project,
                location=self.config.gcp_location,
                temperature=0.2,
                max_output_tokens=1024,
            )
        return self._llm

    def ensure_index_created(self):
        """Creates the vector search index in Valkey if it does not already exist."""
        if self._index_initialized:
            return

        client = self.get_redis_client(decode_responses=True)
        try:
            # Check if index exists
            client.ft(self.index_name).info()
            self._index_initialized = True
            logger.info(f"Valkey index '{self.index_name}' exists.")
        except Exception:
            # Index does not exist -> create it
            try:
                # Embedding dimension is 768 for text-embedding-004
                dim = 768
                create_cmd = [
                    "FT.CREATE",
                    self.index_name,
                    "ON",
                    "HASH",
                    "PREFIX",
                    "1",
                    self.prefix,
                    "SCHEMA",
                    "prompt",
                    "TAG",
                    "response",
                    "TAG",
                    "inserted_at",
                    "NUMERIC",
                    "updated_at",
                    "NUMERIC",
                    "prompt_vector",
                    "VECTOR",
                    "FLAT",
                    "6",
                    "TYPE",
                    "FLOAT32",
                    "DIM",
                    str(dim),
                    "DISTANCE_METRIC",
                    "COSINE",
                ]
                try:
                    client.execute_command(*create_cmd)
                except Exception:
                    # Fallback to pure vector schema
                    fallback_cmd = [
                        "FT.CREATE",
                        self.index_name,
                        "ON",
                        "HASH",
                        "PREFIX",
                        "1",
                        self.prefix,
                        "SCHEMA",
                        "prompt_vector",
                        "VECTOR",
                        "FLAT",
                        "6",
                        "TYPE",
                        "FLOAT32",
                        "DIM",
                        str(dim),
                        "DISTANCE_METRIC",
                        "COSINE",
                    ]
                    client.execute_command(*fallback_cmd)
                self._index_initialized = True
                logger.info(f"Successfully created Valkey vector index: {self.index_name}")
            except Exception as e:
                logger.info(f"Index initialization status: {e}")
                self._index_initialized = True

    def set_threshold(self, threshold: float):
        """Update similarity distance threshold in real-time."""
        self.distance_threshold = threshold

    def set_ttl(self, ttl: int):
        """Update cache TTL in real-time."""
        self.ttl = ttl

    def query(self, prompt: str) -> QueryResult:
        """
        Process a user prompt through Semantic Cache or Vertex AI LLM.
        Measures exact latency and returns rich cache telemetry.
        """
        self.ensure_index_created()
        start_time = time.perf_counter()

        # Step 1: Generate Embedding for the incoming prompt
        emb = self.get_embeddings()
        query_vec = np.array(emb.embed_query(prompt), dtype=np.float32)
        query_vec_norm = query_vec / np.linalg.norm(query_vec)
        query_vec_bytes = query_vec.tobytes()

        # Step 2: Query Valkey for nearest semantic neighbor using Vector KNN
        client = self.get_redis_client(decode_responses=False)
        cmd = [
            "FT.SEARCH",
            self.index_name,
            "*=>[KNN 1 @prompt_vector $vector]",
            "RETURN",
            "3",
            "prompt",
            "response",
            "prompt_vector",
            "DIALECT",
            "2",
            "PARAMS",
            "2",
            "vector",
            query_vec_bytes,
        ]

        try:
            res = client.execute_command(*cmd)
            total = res[0] if isinstance(res, (list, tuple)) and len(res) > 0 else 0
            if total > 0:
                doc_key_raw = res[1]
                hit_key_str = (
                    doc_key_raw.decode("utf-8", errors="ignore")
                    if isinstance(doc_key_raw, bytes)
                    else str(doc_key_raw)
                )
                doc_fields = res[2]
                fields_dict = {}
                for i in range(0, len(doc_fields), 2):
                    f_name = (
                        doc_fields[i].decode("utf-8", errors="ignore")
                        if isinstance(doc_fields[i], bytes)
                        else str(doc_fields[i])
                    )
                    fields_dict[f_name] = doc_fields[i + 1]

                cached_vec_raw = fields_dict.get("prompt_vector")
                if cached_vec_raw and len(cached_vec_raw) >= 768 * 4:
                    cached_vec = np.frombuffer(cached_vec_raw, dtype=np.float32)
                    cached_vec_norm = cached_vec / np.linalg.norm(cached_vec)

                    # Cosine distance = 1.0 - Cosine Similarity
                    cos_sim = float(np.dot(query_vec_norm, cached_vec_norm))
                    cos_dist = max(0.0, 1.0 - cos_sim)

                    # Check if distance is within semantic threshold
                    if cos_dist <= self.distance_threshold:
                        cached_prompt = fields_dict.get("prompt", b"").decode("utf-8", errors="ignore")
                        cached_resp = fields_dict.get("response", b"").decode("utf-8", errors="ignore")
                        similarity_pct = max(0.0, min(100.0, round((1.0 - cos_dist) * 100.0, 1)))

                        # Record cache hit in Valkey Sorted Set
                        hit_count = self.record_cache_hit(hit_key_str)

                        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                        # Persist telemetry metrics in Valkey HASH
                        self.record_telemetry(is_cache_hit=True, latency_ms=elapsed_ms, tokens_saved=250)

                        return QueryResult(
                            answer=cached_resp,
                            is_cache_hit=True,
                            latency_ms=round(elapsed_ms, 2),
                            distance=round(cos_dist, 4),
                            similarity_pct=similarity_pct,
                            matched_prompt=cached_prompt,
                            hit_key=hit_key_str,
                            hit_count=hit_count,
                            prompt_tokens=0,
                            completion_tokens=0,
                            total_tokens=0,
                        )
        except Exception as e:
            logger.warning(f"Valkey vector search error: {e}")

        # Step 3: Cache Miss -> Invoke Vertex AI Gemini
        llm = self.get_llm()
        messages = [
            SystemMessage(content=SUPPORT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]

        response = llm.invoke(messages)
        answer_text = str(response.content)

        # Step 4: Vector-store (prompt, response, prompt_vector) in Valkey
        try:
            entry_id = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
            doc_key = f"{self.prefix}{entry_id}"
            now = time.time()

            hash_data = {
                b"prompt": prompt.encode("utf-8"),
                b"response": answer_text.encode("utf-8"),
                b"prompt_vector": query_vec_bytes,
                b"inserted_at": str(now).encode("utf-8"),
                b"updated_at": str(now).encode("utf-8"),
            }

            client.hset(doc_key, mapping=hash_data)
            if self.ttl and self.ttl > 0:
                client.expire(doc_key, self.ttl)
        except Exception as e:
            logger.warning(f"Failed to store entry in Valkey: {e}")

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Estimate / extract token metrics
        usage = getattr(response, "usage_metadata", None) or {}
        p_tokens = usage.get("input_tokens", int(len(prompt.split()) * 1.3))
        c_tokens = usage.get("output_tokens", int(len(answer_text.split()) * 1.3))
        t_tokens = usage.get("total_tokens", p_tokens + c_tokens)

        # Persist telemetry metrics in Valkey HASH
        self.record_telemetry(is_cache_hit=False, latency_ms=elapsed_ms, tokens_saved=0)

        return QueryResult(
            answer=answer_text,
            is_cache_hit=False,
            latency_ms=round(elapsed_ms, 2),
            distance=None,
            similarity_pct=None,
            matched_prompt=None,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            total_tokens=t_tokens,
        )

    def record_telemetry(
        self,
        is_cache_hit: bool,
        latency_ms: float,
        tokens_saved: int = 250,
        baseline_latency_ms: float = 1200.0,
    ) -> Dict[str, Any]:
        """
        Record and persist a query's telemetry metrics into a dedicated Valkey HASH.
        Returns the updated telemetry dictionary.
        """
        saved_ms = max(0.0, baseline_latency_ms - latency_ms) if is_cache_hit else 0.0
        tokens = tokens_saved if is_cache_hit else 0
        speedup = (baseline_latency_ms / max(latency_ms, 1.0)) if is_cache_hit else 1.0

        try:
            client = self.get_redis_client(decode_responses=True)
            pipe = client.pipeline()
            pipe.hincrby(self.telemetry_key, "total_queries", 1)
            if is_cache_hit:
                pipe.hincrby(self.telemetry_key, "cache_hits", 1)
                if tokens > 0:
                    pipe.hincrby(self.telemetry_key, "tokens_saved", tokens)
                if saved_ms > 0:
                    pipe.hincrbyfloat(self.telemetry_key, "total_time_saved_ms", round(saved_ms, 2))
            else:
                pipe.hincrby(self.telemetry_key, "cache_misses", 1)

            pipe.hset(
                self.telemetry_key,
                mapping={
                    "last_latency_ms": str(round(latency_ms, 2)),
                    "last_was_hit": "1" if is_cache_hit else "0",
                    "last_speedup": str(round(speedup, 2)),
                },
            )
            pipe.execute()
        except Exception as e:
            logger.warning(f"Failed to persist telemetry in Valkey HASH: {e}")

        return self.get_telemetry()

    def get_telemetry(self) -> Dict[str, Any]:
        """
        Retrieve persisted telemetry metrics from the Valkey HASH.
        Returns default zeroed metrics if no entries exist yet.
        """
        defaults = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "tokens_saved": 0,
            "total_time_saved_ms": 0.0,
            "last_latency_ms": 0.0,
            "last_was_hit": False,
            "last_speedup": 1.0,
        }
        try:
            client = self.get_redis_client(decode_responses=True)
            data = client.hgetall(self.telemetry_key)
            if not data:
                return defaults
            return {
                "total_queries": int(data.get("total_queries", 0)),
                "cache_hits": int(data.get("cache_hits", 0)),
                "cache_misses": int(data.get("cache_misses", 0)),
                "tokens_saved": int(data.get("tokens_saved", 0)),
                "total_time_saved_ms": float(data.get("total_time_saved_ms", 0.0)),
                "last_latency_ms": float(data.get("last_latency_ms", 0.0)),
                "last_was_hit": data.get("last_was_hit", "0") in ("1", "true", "True"),
                "last_speedup": float(data.get("last_speedup", 1.0)),
            }
        except Exception as e:
            logger.warning(f"Error fetching telemetry from Valkey: {e}")
            return defaults

    def reset_telemetry(self) -> bool:
        """Reset telemetry metrics stored in the Valkey HASH."""
        try:
            client = self.get_redis_client(decode_responses=True)
            client.delete(self.telemetry_key)
            return True
        except Exception as e:
            logger.warning(f"Error resetting telemetry in Valkey: {e}")
            return False

    def record_cache_hit(self, key_str: str) -> int:
        """
        Increment hit count for a cache key in the leaderboard sorted set.
        Returns the updated total hit count for this key.
        """
        try:
            client = self.get_redis_client(decode_responses=True)
            score = client.zincrby(self.leaderboard_key, 1, key_str)
            return int(score)
        except Exception as e:
            logger.warning(f"Error recording cache hit in sorted set for {key_str}: {e}")
            return 0

    def get_prompt_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve top cached prompts ranked by cache hit count from the sorted set,
        pulling the original prompt text and response from the corresponding Valkey HASH.
        """
        leaderboard = []
        try:
            client = self.get_redis_client(decode_responses=True)
            top_items = client.zrange(self.leaderboard_key, 0, limit - 1, desc=True, withscores=True)

            for rank, (key_str, score) in enumerate(top_items, start=1):
                # Pull prompt and response from the Valkey HASH
                prompt = client.hget(key_str, "prompt")
                response = client.hget(key_str, "response")

                leaderboard.append({
                    "rank": rank,
                    "key": key_str,
                    "hits": int(score),
                    "prompt": prompt or "(Evicted or expired entry)",
                    "response": response or "",
                })
        except Exception as e:
            logger.warning(f"Error retrieving prompt leaderboard: {e}")
        return leaderboard

    def reset_leaderboard(self) -> bool:
        """Reset the leaderboard sorted set in Valkey."""
        try:
            client = self.get_redis_client(decode_responses=True)
            client.delete(self.leaderboard_key)
            return True
        except Exception as e:
            logger.warning(f"Error resetting leaderboard: {e}")
            return False

    def list_cached_entries(self) -> List[Dict[str, Any]]:
        """Retrieve all currently cached entries in Valkey for this prefix."""
        entries = []
        try:
            client = self.get_redis_client(decode_responses=True)
            pattern = f"{self.prefix}*"
            keys = client.keys(pattern)

            for key in keys:
                # Exclude internal telemetry and leaderboard keys
                if key == self.telemetry_key or key == self.leaderboard_key:
                    continue
                key_type = client.type(key)
                ttl = client.ttl(key)
                if key_type == "hash":
                    prompt = client.hget(key, "prompt") or ""
                    response = client.hget(key, "response") or ""
                    # Also fetch hit count from sorted set if available
                    hits = client.zscore(self.leaderboard_key, key)
                    entries.append({
                        "key": key,
                        "prompt": prompt,
                        "response": response,
                        "ttl": ttl if ttl > 0 else "Persistent",
                        "hits": int(hits) if hits is not None else 0,
                    })
        except Exception as e:
            logger.warning(f"Error listing cache entries: {e}")
        return entries

    def delete_entry(self, key: str) -> bool:
        """Delete a single cached entry and remove it from the leaderboard sorted set."""
        try:
            client = self.get_redis_client(decode_responses=True)
            client.delete(key)
            client.zrem(self.leaderboard_key, key)
            return True
        except Exception as e:
            logger.warning(f"Error deleting cache entry {key}: {e}")
            return False

    def clear_cache(self, clear_telemetry: bool = True) -> bool:
        """Clear all entries in the semantic cache and reset leaderboard sorted set & telemetry."""
        try:
            client = self.get_redis_client(decode_responses=True)
            keys = client.keys(f"{self.prefix}*")
            if keys:
                client.delete(*keys)
            client.delete(self.leaderboard_key)
            if clear_telemetry:
                client.delete(self.telemetry_key)
            return True
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
            return False


# Global singleton instance
service = SemanticCacheService()
