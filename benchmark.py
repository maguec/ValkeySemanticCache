#!/usr/bin/env python3
"""
Valkey Semantic Cache Benchmark CLI Runner
-------------------------------------------
Command-line utility to run semantic cache benchmark tests, outputting
structured system-out reports and markdown files.

Usage:
  uv run python benchmark.py
  uv run python benchmark.py --queries 1000 --target-hit-rate 0.80 --report benchmark_report.md
  uv run python benchmark.py --mock  # Fast offline simulation test
"""

import argparse
from benchmark.runner import run_benchmark
from benchmark.reporter import print_benchmark_tables, generate_markdown_report


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark Valkey Semantic Cache with queries targeting ~80% hit rate."
    )
    parser.add_argument(
        "--queries",
        "-n",
        type=int,
        default=1000,
        help="Total number of queries to execute (default: 1000).",
    )
    parser.add_argument(
        "--target-hit-rate",
        "-r",
        type=float,
        default=0.80,
        help="Target cache hit rate between 0.0 and 1.0 (default: 0.80).",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in simulated mock mode (fast, offline, no API quota consumption).",
    )
    parser.add_argument(
        "--no-clear-cache",
        action="store_true",
        help="Do not clear the Valkey cache before starting the benchmark.",
    )
    parser.add_argument(
        "--report",
        type=str,
        default="benchmark_report.md",
        help="File path to save the Markdown benchmark report (default: benchmark_report.md).",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print each query result during execution.",
    )
    args = parser.parse_args()

    summary, _ = run_benchmark(
        queries_count=args.queries,
        target_hit_rate=args.target_hit_rate,
        mock_mode=args.mock,
        clear_cache_first=not args.no_clear_cache,
        verbose=args.verbose,
    )

    # Output system-out formatted report tables
    print_benchmark_tables(summary)

    if args.report:
        generate_markdown_report(summary, args.report)
        print(f"📄 Full Markdown benchmark report exported to: {args.report}")


if __name__ == "__main__":
    main()
