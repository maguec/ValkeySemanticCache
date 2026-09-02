"""
Valkey Semantic Cache Benchmark Package
----------------------------------------
Provides query corpus generation, benchmark execution against Valkey & Vertex AI,
system-out report generation, and NiceGUI web application interface.
"""

from .corpus import TOPIC_TEMPLATES, expand_topics_corpus, generate_benchmark_questions
from .runner import BenchmarkItemResult, BenchmarkSummary, run_benchmark
from .reporter import generate_stdout_report, print_benchmark_tables, generate_markdown_report

__all__ = [
    "TOPIC_TEMPLATES",
    "expand_topics_corpus",
    "generate_benchmark_questions",
    "BenchmarkItemResult",
    "BenchmarkSummary",
    "run_benchmark",
    "generate_stdout_report",
    "print_benchmark_tables",
    "generate_markdown_report",
]
