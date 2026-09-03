"""
System-Out and Markdown report generator for Valkey Semantic Cache Benchmark.
"""

from typing import Optional, Callable
from config import config
from .runner import BenchmarkSummary


def generate_stdout_report(summary: BenchmarkSummary) -> str:
    """
    Renders clean, structured ASCII system-out tables tabulating the benchmark results.
    Returns the report as a formatted multi-line string.
    """
    line_sep = "=" * 86
    sub_sep = "-" * 86

    lines = []
    lines.append(line_sep)
    lines.append("                    VALKEY SEMANTIC CACHE BENCHMARK RESULTS")
    lines.append(line_sep)

    # Main 3 Requested Target Metrics Table
    lines.append("\n" + sub_sep)
    lines.append(f"🎯 PRIMARY TELEMETRY KPI SUMMARY ({summary.total_queries:,} QUERIES)")
    lines.append(sub_sep)
    lines.append(f"| {'Metric':<30} | {'Value':<18} | {'Details & Breakdown':<30} |")
    lines.append(f"+{'-'*32}+{'-'*20}+{'-'*32}+")
    lines.append(f"| {'Cache Hit Rate':<30} | {summary.cache_hit_rate_pct:>6.2f}%{'':<11} | {summary.cache_hits:,} Hits / {summary.total_queries:,} Total Queries{'':<2} |")
    lines.append(f"| {'% of Tokens Saved':<30} | {summary.pct_tokens_saved:>6.2f}%{'':<11} | {summary.total_tokens_saved:,} Saved / {summary.total_hypothetical_tokens:,} Total{'':<1} |")
    lines.append(f"| {'% of Time Saved':<30} | {summary.pct_time_saved:>6.2f}%{'':<11} | {summary.total_time_saved_ms/1000.0:>6.1f}s Saved / {summary.total_hypothetical_latency_ms/1000.0:>6.1f}s Base{'':<1} |")
    lines.append(f"+{'-'*32}+{'-'*20}+{'-'*32}+")

    # Latency & Speedup Breakdown
    lines.append("\n" + sub_sep)
    lines.append("⚡ LATENCY & SPEEDUP BREAKDOWN")
    lines.append(sub_sep)
    lines.append(f"| {'Metric':<42} | {'Measurement':<39} |")
    lines.append(f"+{'-'*44}+{'-'*41}+")
    lines.append(f"| {'Average Cache Hit Latency':<42} | {summary.avg_hit_latency_ms:>8.2f} ms (Valkey Vector KNN){'':<13} |")
    lines.append(f"| {'Average Cache Miss Latency':<42} | {summary.avg_miss_latency_ms:>8.2f} ms (Gemini LLM Call){'':<14} |")
    lines.append(f"| {'Latency Speedup Factor':<42} | {summary.speedup_factor:>8.1f}x faster on Cache Hits{'':<12} |")
    lines.append(f"| {'Overall Average Query Latency':<42} | {summary.overall_avg_latency_ms:>8.2f} ms{'':<33} |")
    lines.append(f"| {'Total Time Saved by Caching':<42} | {summary.total_time_saved_ms / 1000.0:>8.1f} seconds ({summary.pct_time_saved:.1f}% saved){'':<9} |")
    lines.append(f"| {'Benchmark Total Wall-Clock Time':<42} | {summary.total_wall_clock_sec:>8.1f} seconds{'':<28} |")
    lines.append(f"+{'-'*44}+{'-'*41}+")

    # Token Consumption Breakdown
    lines.append("\n" + sub_sep)
    lines.append("🪙 TOKEN CONSUMPTION & COST SAVINGS BREAKDOWN")
    lines.append(sub_sep)
    lines.append(f"| {'Metric':<42} | {'Token Count':<39} |")
    lines.append(f"+{'-'*44}+{'-'*41}+")
    lines.append(f"| {'Actual Tokens Billed (LLM Misses)':<42} | {summary.total_actual_tokens:>10,} tokens{'':<22} |")
    lines.append(f"| {'Tokens Saved by Valkey Cache':<42} | {summary.total_tokens_saved:>10,} tokens ({summary.pct_tokens_saved:.1f}% saved){'':<5} |")
    lines.append(f"| {'Hypothetical Tokens without Cache':<42} | {summary.total_hypothetical_tokens:>10,} tokens{'':<22} |")
    lines.append(f"+{'-'*44}+{'-'*41}+")

    # Category Breakdown Table
    lines.append("\n" + sub_sep)
    lines.append("📂 BREAKDOWN BY SUPPORT TOPIC CATEGORY")
    lines.append(sub_sep)
    lines.append(f"| {'Category':<28} | {'Queries':<8} | {'Hits':<6} | {'Hit %':<8} | {'Tokens Saved':<13} | {'Time Saved':<11} |")
    lines.append(f"+{'-'*30}+{'-'*10}+{'-'*8}+{'-'*10}+{'-'*15}+{'-'*13}+")
    for cat_name, cs in sorted(summary.category_stats.items()):
        cat_hit_pct = (cs["hits"] / cs["queries"] * 100.0) if cs["queries"] > 0 else 0.0
        lines.append(
            f"| {cat_name:<28} | {cs['queries']:>8} | {cs['hits']:>6} | {cat_hit_pct:>7.1f}% | "
            f"{cs['tokens_saved']:>13,} | {cs['time_saved_ms'] / 1000.0:>9.1f}s |"
        )
    lines.append(f"+{'-'*30}+{'-'*10}+{'-'*8}+{'-'*10}+{'-'*15}+{'-'*13}+")
    lines.append(line_sep + "\n")

    return "\n".join(lines)


def print_benchmark_tables(summary: BenchmarkSummary, log_callback: Optional[Callable[[str], None]] = None):
    """
    Prints system-out report directly to stdout or via log_callback.
    """
    report_text = generate_stdout_report(summary)
    if log_callback:
        log_callback(report_text)
    else:
        print(report_text)


def generate_markdown_report(summary: BenchmarkSummary, filepath: str):
    """Generates a detailed GitHub-flavored Markdown report."""
    md = f"""# 🚀 Valkey Semantic Cache Benchmark Report

**Benchmark Configuration:**
- **Total Queries Executed:** {summary.total_queries:,}
- **Target Hit Rate:** {summary.cache_hit_rate_pct:.1f}%
- **Distance Threshold:** `{config.distance_threshold}`
- **Embedding Model:** `{config.vertex_embedding_model}`
- **Vertex AI Model:** `{config.vertex_model}`
- **Total Runtime:** {summary.total_wall_clock_sec:.1f}s

---

## 🎯 Primary Telemetry KPI Summary

| Metric | Result | Breakdown / Details |
| :--- | :---: | :--- |
| **Cache Hit Rate** | **`{summary.cache_hit_rate_pct:.2f}%`** | {summary.cache_hits:,} Hits / {summary.total_queries:,} Total Queries ({summary.cache_misses:,} Misses) |
| **% of Tokens Saved** | **`{summary.pct_tokens_saved:.2f}%`** | {summary.total_tokens_saved:,} Tokens Saved / {summary.total_hypothetical_tokens:,} Total Hypothetical |
| **% of Time Saved** | **`{summary.pct_time_saved:.2f}%`** | {summary.total_time_saved_ms / 1000.0:.1f}s Saved / {summary.total_hypothetical_latency_ms / 1000.0:.1f}s Total Hypothetical |

---

## ⚡ Latency & Speedup Breakdown

| Metric | Measurement | Notes |
| :--- | :---: | :--- |
| **Avg Cache Hit Latency** | `{summary.avg_hit_latency_ms:.2f} ms` | Sub-millisecond vector KNN search in Valkey |
| **Avg Cache Miss Latency** | `{summary.avg_miss_latency_ms:.2f} ms` | Full Vertex AI LLM round-trip |
| **Latency Speedup** | **`{summary.speedup_factor:.1f}x`** | Speedup factor on cache hits |
| **Overall Mean Latency** | `{summary.overall_avg_latency_ms:.2f} ms` | Blended average across all 1,000 requests |
| **Total Latency Saved** | `{summary.total_time_saved_ms / 1000.0:.1f} seconds` | Total compute wait time eliminated |

---

## 🪙 Token Consumption & Cost Breakdown

| Metric | Tokens | Impact |
| :--- | :---: | :--- |
| **Actual Tokens Billed** | `{summary.total_actual_tokens:,}` | Tokens consumed by Gemini on cache misses |
| **Tokens Saved by Cache** | **`{summary.total_tokens_saved:,}`** | **{summary.pct_tokens_saved:.1f}% reduction** in LLM token usage |
| **Hypothetical Tokens (No Cache)** | `{summary.total_hypothetical_tokens:,}` | Total tokens if every query hit Gemini |

---

## 📂 Topic Category Breakdown

| Category | Queries | Hits | Misses | Hit Rate | Tokens Saved | Time Saved |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
"""

    for cat_name, cs in sorted(summary.category_stats.items()):
        cat_hit_pct = (cs["hits"] / cs["queries"] * 100.0) if cs["queries"] > 0 else 0.0
        md += f"| **{cat_name}** | {cs['queries']} | {cs['hits']} | {cs['misses']} | `{cat_hit_pct:.1f}%` | {cs['tokens_saved']:,} | {cs['time_saved_ms']/1000.0:.1f}s |\n"

    md += """
---
*Generated automatically by `benchmark` package with Valkey Semantic Cache.*
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)
