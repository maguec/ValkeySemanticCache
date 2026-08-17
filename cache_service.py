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
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class CacheEntry:
    key: str
    prompt: str
    response: str
    ttl: Optional[int] = None


class SemanticCacheService:
    def __init__(self):
        self.config = config
        self.distance_threshold = config.distance_threshold
        self.ttl = config.cache_ttl
        self.index_name = f"{config.cache_index_name}:{config.cache_prefix}"
        self.prefix = f"{self.index_name}:"
        self._raw_client: Optional[redis.Redis] = None
        self._text_client: Optional[redis.Redis] = None
        self._embeddings: Optional[GoogleGenerativeAIEmbeddings] = None
        self._llm: Optional[ChatGoogleGenerativeAI] = None
        self._index_initialized: bool = False

    def get_redis_client(self, decode_responses: bool = False) -> redis.Redis:
        """Get or initialize raw or text Redis/Valkey client."""
        url = self.config.get_redis_connection_url()
        if decode_responses:
            if self._text_client is None:
                self._text_client = redis.Redis.from_url(
                    url,
                    decode_responses=True,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                )
            return self._text_client
        else:
            if self._raw_client is None:
                self._raw_client = redis.Redis.from_url(
                    url,
                    decode_responses=False,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                )
            return self._raw_client

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
                    "TEXT",
                    "response",
                    "TEXT",
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
                client.execute_command(*create_cmd)
                self._index_initialized = True
                logger.info(f"Successfully created Valkey vector index: {self.index_name}")
            except Exception as e:
                logger.warning(f"Index creation notice: {e}")
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
                doc_fields = res[2]
                fields_dict = {}
                for i in range(0, len(doc_fields), 2):
                    key_str = (
                        doc_fields[i].decode("utf-8", errors="ignore")
                        if isinstance(doc_fields[i], bytes)
                        else str(doc_fields[i])
                    )
                    fields_dict[key_str] = doc_fields[i + 1]

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

                        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                        return QueryResult(
                            answer=cached_resp,
                            is_cache_hit=True,
                            latency_ms=round(elapsed_ms, 2),
                            distance=round(cos_dist, 4),
                            similarity_pct=similarity_pct,
                            matched_prompt=cached_prompt,
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

    def list_cached_entries(self) -> List[Dict[str, Any]]:
        """Retrieve all currently cached entries in Valkey for this prefix."""
        entries = []
        try:
            client = self.get_redis_client(decode_responses=True)
            pattern = f"{self.prefix}*"
            keys = client.keys(pattern)

            for key in keys:
                key_type = client.type(key)
                ttl = client.ttl(key)
                if key_type == "hash":
                    prompt = client.hget(key, "prompt") or ""
                    response = client.hget(key, "response") or ""
                    entries.append({
                        "key": key,
                        "prompt": prompt,
                        "response": response,
                        "ttl": ttl if ttl > 0 else "Persistent",
                    })
        except Exception as e:
            logger.warning(f"Error listing cache entries: {e}")
        return entries

    def delete_entry(self, key: str) -> bool:
        """Delete a single cached entry."""
        try:
            client = self.get_redis_client(decode_responses=True)
            client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Error deleting cache entry {key}: {e}")
            return False

    def clear_cache(self) -> bool:
        """Clear all entries in the semantic cache."""
        try:
            client = self.get_redis_client(decode_responses=True)
            keys = client.keys(f"{self.prefix}*")
            if keys:
                client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
            return False


# Global singleton instance
service = SemanticCacheService()
