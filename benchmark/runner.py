"""
Execution runner and metrics collector for Valkey Semantic Cache Benchmark.
"""

import sys
import time
import random
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional, Callable

from cache_service import service, QueryResult
from .corpus import generate_benchmark_questions


@dataclass
class BenchmarkItemResult:
    index: int
    prompt: str
    category: str
    is_cache_hit: bool
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    tokens_saved: int
    distance: Optional[float]
    time_saved_ms: float


@dataclass
class BenchmarkSummary:
    total_queries: int
    cache_hits: int
    cache_misses: int
    cache_hit_rate_pct: float
    total_actual_tokens: int
    total_tokens_saved: int
    total_hypothetical_tokens: int
    pct_tokens_saved: float
    total_actual_latency_ms: float
    total_time_saved_ms: float
    total_hypothetical_latency_ms: float
    pct_time_saved: float
    avg_hit_latency_ms: float
    avg_miss_latency_ms: float
    overall_avg_latency_ms: float
    speedup_factor: float
    category_stats: Dict[str, Dict[str, Any]]
    total_wall_clock_sec: float


def run_benchmark(
    queries_count: int = 1000,
    target_hit_rate: float = 0.80,
    mock_mode: bool = False,
    clear_cache_first: bool = True,
    verbose: bool = False,
    progress_callback: Optional[Callable[[int, int, BenchmarkItemResult, Dict[str, Any]], None]] = None,
    log_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[BenchmarkSummary, List[BenchmarkItemResult]]:
    """
    Executes queries through the Semantic Cache, records metrics,
    and returns the summarized results.
    """
    def log(msg: str):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    log(f"\n{'='*86}")
    log(f"🚀 INITIALIZING VALKEY SEMANTIC CACHE BENCHMARK")
    log(f"{'='*86}")
    log(f"• Total Queries:      {queries_count:,}")
    log(f"• Target Hit Rate:    {target_hit_rate * 100:.1f}%")
    log(f"• Mode:               {'SIMULATION (Mock LLM)' if mock_mode else 'LIVE (Valkey + Vertex AI)'}")
    log(f"• Distance Threshold: {service.distance_threshold:.2f}")
    log(f"• Clear Cache First:  {clear_cache_first}")
    log(f"{'='*86}\n")

    if clear_cache_first and not mock_mode:
        log("🧹 Clearing Valkey Semantic Cache & Telemetry HASH...")
        service.clear_cache(clear_telemetry=True)
        log("✓ Valkey Semantic Cache cleared.\n")

    questions = generate_benchmark_questions(total_queries=queries_count, target_hit_rate=target_hit_rate)
    log(f"✓ Generated {len(questions):,} benchmark queries across diverse support domains.\n")

    results: List[BenchmarkItemResult] = []
    start_bench_time = time.perf_counter()

    hits_count = 0
    misses_count = 0
    running_tokens_saved = 0
    running_time_saved_ms = 0.0

    sim_cache: Dict[str, Dict[str, Any]] = {}
    topic_miss_latencies: Dict[str, float] = {}

    for idx, (prompt, expected_hit, category) in enumerate(questions, start=1):
        topic_key = prompt.split()[0].lower() + "_" + prompt.split()[-1].lower()

        if mock_mode:
            # Simulated cache behavior matching real Valkey + Gemini characteristics
            if expected_hit and len(sim_cache) > 0:
                is_hit = True
                latency_ms = random.uniform(8.5, 25.0)  # Valkey KNN search latency
                tokens_saved = random.randint(180, 420)
                original_latency = topic_miss_latencies.get(topic_key, random.uniform(950.0, 1450.0))
                time_saved_ms = max(0.0, original_latency - latency_ms)
                p_tokens, c_tokens, t_tokens = 0, 0, 0
                dist = random.uniform(0.04, 0.16)
            else:
                is_hit = False
                latency_ms = random.uniform(900.0, 1400.0)  # Gemini LLM latency
                p_tokens = int(len(prompt.split()) * 1.3) + random.randint(15, 30)
                c_tokens = random.randint(150, 350)
                t_tokens = p_tokens + c_tokens
                tokens_saved = 0
                time_saved_ms = 0.0
                dist = None
                sim_cache[topic_key] = {"tokens": t_tokens, "latency": latency_ms}
                topic_miss_latencies[topic_key] = latency_ms
        else:
            # LIVE EXECUTION against Valkey and Vertex AI
            q_res: QueryResult = service.query(prompt)
            is_hit = q_res.is_cache_hit
            latency_ms = q_res.latency_ms
            p_tokens = q_res.prompt_tokens
            c_tokens = q_res.completion_tokens
            t_tokens = q_res.total_tokens
            tokens_saved = getattr(q_res, "tokens_saved", 250 if is_hit else 0)

            dist = q_res.distance

            if not is_hit:
                topic_miss_latencies[topic_key] = latency_ms
                time_saved_ms = 0.0
            else:
                baseline = topic_miss_latencies.get(topic_key, 1200.0)
                time_saved_ms = max(0.0, baseline - latency_ms)

        if is_hit:
            hits_count += 1
            running_tokens_saved += tokens_saved
            running_time_saved_ms += time_saved_ms
        else:
            misses_count += 1

        item_result = BenchmarkItemResult(
            index=idx,
            prompt=prompt,
            category=category,
            is_cache_hit=is_hit,
            latency_ms=latency_ms,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            total_tokens=t_tokens,
            tokens_saved=tokens_saved,
            distance=dist,
            time_saved_ms=time_saved_ms,
        )
        results.append(item_result)

        elapsed_sec = time.perf_counter() - start_bench_time
        current_summary = {
            "index": idx,
            "queries_count": queries_count,
            "hits": hits_count,
            "misses": misses_count,
            "hit_rate_pct": (hits_count / idx) * 100.0,
            "tokens_saved": running_tokens_saved,
            "time_saved_ms": running_time_saved_ms,
            "elapsed_sec": elapsed_sec,
        }

        # Progress update every 10 queries or last query
        if idx % 10 == 0 or idx == queries_count:
            curr_pct = (idx / queries_count) * 100.0
            curr_hit_rate = (hits_count / idx) * 100.0
            status_line = (
                f"[{idx:>4}/{queries_count}] ({curr_pct:>5.1f}%) | "
                f"⚡ Hits: {hits_count:>4} ({curr_hit_rate:>5.1f}%) | "
                f"🔴 Misses: {misses_count:>3} | "
                f"🪙 Tokens Saved: {running_tokens_saved:>6,} | "
                f"⏱️ Time Saved: {running_time_saved_ms / 1000:>6.1f}s | "
                f"Elapsed: {elapsed_sec:>5.1f}s"
            )

            if log_callback:
                log_callback(status_line)
            else:
                sys.stdout.write(f"\r{status_line}")
                sys.stdout.flush()

        if verbose:
            tag = "⚡ HIT " if is_hit else "🔴 MISS"
            log(f"  [{idx:>4}] {tag} ({latency_ms:6.1f}ms) | {prompt[:65]}...")

        if progress_callback:
            progress_callback(idx, queries_count, item_result, current_summary)

    total_wall_clock = time.perf_counter() - start_bench_time
    log("\n\n✓ Benchmark run complete!\n")

    # Aggregate Metrics
    total_q = len(results)
    hits = sum(1 for r in results if r.is_cache_hit)
    misses = total_q - hits
    hit_rate_pct = (hits / total_q * 100.0) if total_q > 0 else 0.0

    total_actual_tokens = sum(r.total_tokens for r in results)
    total_tokens_saved = sum(r.tokens_saved for r in results)
    total_hypo_tokens = total_actual_tokens + total_tokens_saved
    pct_tokens_saved = (total_tokens_saved / total_hypo_tokens * 100.0) if total_hypo_tokens > 0 else 0.0

    total_actual_lat_ms = sum(r.latency_ms for r in results)
    total_time_saved_ms = sum(r.time_saved_ms for r in results)
    total_hypo_lat_ms = total_actual_lat_ms + total_time_saved_ms
    pct_time_saved = (total_time_saved_ms / total_hypo_lat_ms * 100.0) if total_hypo_lat_ms > 0 else 0.0

    hit_latencies = [r.latency_ms for r in results if r.is_cache_hit]
    miss_latencies = [r.latency_ms for r in results if not r.is_cache_hit]

    avg_hit_lat = (sum(hit_latencies) / len(hit_latencies)) if hit_latencies else 0.0
    avg_miss_lat = (sum(miss_latencies) / len(miss_latencies)) if miss_latencies else 0.0
    overall_avg_lat = (total_actual_lat_ms / total_q) if total_q > 0 else 0.0
    speedup = (avg_miss_lat / max(avg_hit_lat, 0.1)) if avg_hit_lat > 0 else 1.0

    # Category Stats
    cat_stats: Dict[str, Dict[str, Any]] = {}
    for r in results:
        if r.category not in cat_stats:
            cat_stats[r.category] = {
                "queries": 0,
                "hits": 0,
                "misses": 0,
                "tokens_saved": 0,
                "time_saved_ms": 0.0,
                "latencies": [],
            }
        cs = cat_stats[r.category]
        cs["queries"] += 1
        if r.is_cache_hit:
            cs["hits"] += 1
        else:
            cs["misses"] += 1
        cs["tokens_saved"] += r.tokens_saved
        cs["time_saved_ms"] += r.time_saved_ms
        cs["latencies"].append(r.latency_ms)

    summary = BenchmarkSummary(
        total_queries=total_q,
        cache_hits=hits,
        cache_misses=misses,
        cache_hit_rate_pct=hit_rate_pct,
        total_actual_tokens=total_actual_tokens,
        total_tokens_saved=total_tokens_saved,
        total_hypothetical_tokens=total_hypo_tokens,
        pct_tokens_saved=pct_tokens_saved,
        total_actual_latency_ms=total_actual_lat_ms,
        total_time_saved_ms=total_time_saved_ms,
        total_hypothetical_latency_ms=total_hypo_lat_ms,
        pct_time_saved=pct_time_saved,
        avg_hit_latency_ms=avg_hit_lat,
        avg_miss_latency_ms=avg_miss_lat,
        overall_avg_latency_ms=overall_avg_lat,
        speedup_factor=speedup,
        category_stats=cat_stats,
        total_wall_clock_sec=total_wall_clock,
    )

    return summary, results
