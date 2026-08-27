# 🚀 Valkey Semantic Cache Benchmark Report

**Benchmark Configuration:**
- **Total Queries Executed:** 1,000
- **Target Hit Rate:** 80.0%
- **Distance Threshold:** `0.2`
- **Embedding Model:** `text-embedding-004`
- **Vertex AI Model:** `gemini-2.5-flash`
- **Total Runtime:** 0.0s

---

## 🎯 Primary Telemetry KPI Summary

| Metric | Result | Breakdown / Details |
| :--- | :---: | :--- |
| **Cache Hit Rate** | **`80.00%`** | 800 Hits / 1,000 Total Queries (200 Misses) |
| **% of Tokens Saved** | **`80.52%`** | 237,766 Tokens Saved / 295,281 Total Hypothetical |
| **% of Time Saved** | **`79.66%`** | 945.9s Saved / 1187.3s Total Hypothetical |

---

## ⚡ Latency & Speedup Breakdown

| Metric | Measurement | Notes |
| :--- | :---: | :--- |
| **Avg Cache Hit Latency** | `16.61 ms` | Sub-millisecond vector KNN search in Valkey |
| **Avg Cache Miss Latency** | `1140.81 ms` | Full Vertex AI LLM round-trip |
| **Latency Speedup** | **`68.7x`** | Speedup factor on cache hits |
| **Overall Mean Latency** | `241.45 ms` | Blended average across all 1,000 requests |
| **Total Latency Saved** | `945.9 seconds` | Total compute wait time eliminated |

---

## 🪙 Token Consumption & Cost Breakdown

| Metric | Tokens | Impact |
| :--- | :---: | :--- |
| **Actual Tokens Billed** | `57,515` | Tokens consumed by Gemini on cache misses |
| **Tokens Saved by Cache** | **`237,766`** | **80.5% reduction** in LLM token usage |
| **Hypothetical Tokens (No Cache)** | `295,281` | Total tokens if every query hit Gemini |

---

## 📂 Topic Category Breakdown

| Category | Queries | Hits | Misses | Hit Rate | Tokens Saved | Time Saved |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **API & Rate Limits** | 52 | 47 | 5 | `90.4%` | 14,471 | 57.0s |
| **Authentication & Security** | 86 | 80 | 6 | `93.0%` | 24,462 | 95.2s |
| **Billing & Subscriptions** | 95 | 87 | 8 | `91.6%` | 25,374 | 102.9s |
| **Data & Compliance** | 46 | 42 | 4 | `91.3%` | 13,209 | 48.2s |
| **Performance & SLA** | 24 | 21 | 3 | `87.5%` | 6,834 | 23.8s |
| **Platform Configuration** | 658 | 488 | 170 | `74.2%` | 143,117 | 578.3s |
| **Team Management** | 39 | 35 | 4 | `89.7%` | 10,299 | 40.4s |

---
*Generated automatically by `benchmark.py` with Valkey Semantic Cache.*
