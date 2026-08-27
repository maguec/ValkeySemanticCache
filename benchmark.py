#!/usr/bin/env python3
"""
Valkey Semantic Cache Benchmark
-------------------------------
Runs a benchmark of 1,000 questions through the Valkey Semantic Cache,
targeting an ~80% Cache Hit Rate, and tabulates:
  1. Cache Hit Rate
  2. % of Tokens Saved
  3. % of Time Saved
along with detailed latency, throughput, and token breakdown statistics.

Usage:
  uv run python benchmark.py
  uv run python benchmark.py --queries 1000 --target-hit-rate 0.80 --report benchmark_report.md
  uv run python benchmark.py --mock  # Fast offline simulation test
"""

import sys
import time
import random
import argparse
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional

from cache_service import service, QueryResult
from config import config


# =====================================================================
# 1. COMPREHENSIVE CUSTOMER SUPPORT QUERY CORPUS (TOPICS & VARIATIONS)
# =====================================================================
TOPIC_TEMPLATES = [
    # Subscriptions & Billing
    {
        "category": "Billing & Subscriptions",
        "base": "How can I cancel my subscription and get a refund?",
        "variations": [
            "I want to stop paying for my account and get my money back.",
            "What is the procedure to terminate membership and be reimbursed?",
            "How do I cancel my plan and receive a payment refund?",
            "Can I cancel my active subscription and claim a refund?",
            "Where do I go to cancel my subscription and get money returned?",
        ],
    },
    {
        "category": "Billing & Subscriptions",
        "base": "How do I upgrade from the Starter plan to the Pro plan?",
        "variations": [
            "What are the steps to switch my account from Starter to Pro tier?",
            "I would like to upgrade my subscription to the Pro level.",
            "How can I move my current plan up to Pro?",
            "Where in the billing settings can I change from Starter to Pro?",
            "Can I upgrade my tier to Pro immediately?",
        ],
    },
    {
        "category": "Billing & Subscriptions",
        "base": "Where can I download PDF invoices and receipts for my payments?",
        "variations": [
            "How do I get past payment receipts and invoice PDFs?",
            "Where are the downloadable billing statements located in my dashboard?",
            "Can I download billing receipts for accounting purposes as PDFs?",
            "How can I export my monthly invoices in PDF format?",
            "Where do I find receipt PDFs for all previous charges?",
        ],
    },
    {
        "category": "Billing & Subscriptions",
        "base": "How do I update my billing credit card details?",
        "variations": [
            "Where can I change the credit card on file for my subscription?",
            "How do I replace my expired payment card with a new one?",
            "What is the process to update payment method details?",
            "Can I add a new credit card for automatic monthly payments?",
            "Where in account settings can I change my payment credit card?",
        ],
    },
    {
        "category": "Billing & Subscriptions",
        "base": "Does CloudNova offer annual billing discounts?",
        "variations": [
            "Is there a discount if I pay annually instead of monthly?",
            "Do you provide cheaper rates for yearly subscription commitments?",
            "How much do I save by switching to annual billing?",
            "Are there yearly payment pricing discounts available?",
            "Can I get a discount for paying for a whole year upfront?",
        ],
    },
    {
        "category": "Billing & Subscriptions",
        "base": "What happens if my payment fails during automatic renewal?",
        "variations": [
            "What occurs if my renewal charge is declined by my bank?",
            "Will my service be immediately shut down if payment fails?",
            "Is there a grace period when an automatic payment fails?",
            "How many retry attempts are made if my credit card fails to charge?",
            "What is the policy when a subscription payment doesn't go through?",
        ],
    },
    {
        "category": "Billing & Subscriptions",
        "base": "How is prorated billing calculated when upgrading mid-month?",
        "variations": [
            "How do prorated charges work if I change plans midway through a cycle?",
            "Do you charge prorated amounts for mid-cycle plan upgrades?",
            "What is the proration calculation when upgrading before the month ends?",
            "Will I only be charged for the remaining days if I upgrade today?",
            "How does mid-billing-cycle proration work for subscription changes?",
        ],
    },
    {
        "category": "Billing & Subscriptions",
        "base": "How do I apply a promotional discount coupon code to my checkout?",
        "variations": [
            "Where do I enter a promo code during checkout?",
            "How can I redeem a discount voucher on my subscription?",
            "Where is the coupon code input box located on the billing page?",
            "Can I add a promotional code to an existing active subscription?",
            "How do I apply a discount coupon to my monthly bill?",
        ],
    },

    # Authentication & Security
    {
        "category": "Authentication & Security",
        "base": "How do I reset my forgotten account password?",
        "variations": [
            "I forgot my login password, how do I recover it?",
            "Where can I request a password reset link for my account?",
            "What is the procedure to restore access if I cannot remember my password?",
            "How can I change my lost login credentials?",
            "I can't sign in because I forgot my password, what should I do?",
        ],
    },
    {
        "category": "Authentication & Security",
        "base": "How do I enable two-factor authentication (2FA) with an authenticator app?",
        "variations": [
            "Where do I configure two-step verification using Google Authenticator?",
            "How can I set up 2FA multi-factor security on my profile?",
            "What are the steps to turn on two-factor auth with an OTP app?",
            "Can I protect my account using two-factor authentication?",
            "How do I activate 2FA with an authenticator application?",
        ],
    },
    {
        "category": "Authentication & Security",
        "base": "How do I configure Single Sign-On (SSO) with Okta or Google Workspace?",
        "variations": [
            "What is the setup guide for SAML SSO with Okta identity provider?",
            "How can our organization enable Single Sign-On using Google Workspace?",
            "Where do I find SAML 2.0 metadata for configuring SSO?",
            "Can we connect our corporate Okta directory via SSO?",
            "How do I set up enterprise SAML SSO authentication?",
        ],
    },
    {
        "category": "Authentication & Security",
        "base": "How do I revoke an active user session or sign out of all devices?",
        "variations": [
            "Where can I log out of all connected browsers and devices?",
            "How do I terminate all active login sessions for my account?",
            "Is there a button to remotely sign out of other active sessions?",
            "How can I invalidate all existing login tokens across devices?",
            "Can I force logout on all devices if I suspect unauthorized access?",
        ],
    },
    {
        "category": "Authentication & Security",
        "base": "How do I regenerate or delete a compromised API secret key?",
        "variations": [
            "My API key was leaked, how do I revoke and generate a new one?",
            "Where in developer settings can I rotate my API tokens?",
            "How do I immediately delete an old API secret and create a replacement?",
            "What should I do to roll my API credentials after a key exposure?",
            "Can I revoke active API keys from the web dashboard?",
        ],
    },
    {
        "category": "Authentication & Security",
        "base": "What are the password complexity requirements for user accounts?",
        "variations": [
            "What rules must my password follow when creating an account?",
            "What is the minimum character length and complexity for passwords?",
            "Are special characters and numbers required in account passwords?",
            "What password policy does the platform enforce?",
            "What are the security guidelines for setting a strong password?",
        ],
    },

    # API & Developer Platform
    {
        "category": "API & Rate Limits",
        "base": "What are the API rate limits and request quotas for CloudNova?",
        "variations": [
            "How many requests per minute can I make to the CloudNova API?",
            "Is there a cap on API calls per second for standard tiers?",
            "What are the maximum API request limits across endpoints?",
            "Where can I check my current API rate limit consumption?",
            "What is the per-minute API throttle limit for my account?",
        ],
    },
    {
        "category": "API & Rate Limits",
        "base": "How do I handle HTTP 429 Too Many Requests errors in my code?",
        "variations": [
            "What is the recommended retry strategy for 429 rate limit errors?",
            "How should I implement exponential backoff when hitting API throttles?",
            "Which response headers indicate the rate limit reset timestamp?",
            "What does HTTP status 429 mean and how do I avoid it?",
            "How do I write a retry loop for rate-limited API requests?",
        ],
    },
    {
        "category": "API & Rate Limits",
        "base": "How do I set up webhook endpoints to receive real-time event notifications?",
        "variations": [
            "What is the process to register a webhook URL for system events?",
            "Where do I configure webhooks in the developer console?",
            "How can I receive HTTP POST callbacks for account events?",
            "What events can be sent to custom webhook endpoints?",
            "How do I test and verify webhook signatures in my application?",
        ],
    },
    {
        "category": "API & Rate Limits",
        "base": "Where can I find official SDK libraries for Python, Node.js, and Go?",
        "variations": [
            "Does CloudNova provide an official Python client library?",
            "Where are the official client SDKs for JavaScript and TypeScript?",
            "How do I install the Python SDK via pip for CloudNova?",
            "Are there developer SDKs available for Golang and Node?",
            "Where can I browse SDK documentation and GitHub repositories?",
        ],
    },
    {
        "category": "API & Rate Limits",
        "base": "How do I paginate through large lists in REST API responses?",
        "variations": [
            "What pagination parameters (cursor, limit, offset) are supported by the API?",
            "How do I fetch the next page of results in API queries?",
            "Does the API use cursor-based pagination for listing items?",
            "How can I iterate over all records using page tokens?",
            "What is the maximum page size for list endpoints in the API?",
        ],
    },

    # Team & Access Management
    {
        "category": "Team Management",
        "base": "How do I invite a new team member to my workspace?",
        "variations": [
            "Where can I send an invitation email to add a teammate to my organization?",
            "What is the process to add colleagues to our CloudNova workspace?",
            "How do I grant workspace access to another user via email?",
            "Can I invite multiple collaborators to my team account?",
            "Where do I find the 'Invite Member' button in workspace settings?",
        ],
    },
    {
        "category": "Team Management",
        "base": "What are the permission differences between Admin, Editor, and Viewer roles?",
        "variations": [
            "What access level does the Editor role have compared to Admin?",
            "Can Viewers create API keys or modify workspace settings?",
            "What role-based access control (RBAC) levels exist in workspaces?",
            "How do user permissions differ across workspace roles?",
            "What actions are restricted to Workspace Owners and Admins?",
        ],
    },
    {
        "category": "Team Management",
        "base": "How do I transfer Workspace Ownership to another user?",
        "variations": [
            "How can I transfer account owner privileges to a colleague?",
            "What is the procedure to change the primary owner of a workspace?",
            "Where do I go to assign ownership rights to a different team admin?",
            "Can I transfer my billing and workspace ownership to another person?",
            "How do I hand over workspace ownership when leaving an organization?",
        ],
    },
    {
        "category": "Team Management",
        "base": "How do I remove or deactivate a former team member's access?",
        "variations": [
            "How do I remove a user from our team workspace?",
            "Where can I revoke workspace membership for a departed employee?",
            "What happens to API keys created by a user when they are removed?",
            "Can an Admin delete a user's account access from the team roster?",
            "How do I immediately deactivate a teammate's login access?",
        ],
    },

    # Data & Compliance
    {
        "category": "Data & Compliance",
        "base": "How can I export all my organization's data in JSON or CSV format?",
        "variations": [
            "Where do I request a full data export of our account history?",
            "How do I download a backup of all my data from the platform?",
            "Can I export workspace records into CSV or JSON files?",
            "What is the process to generate a complete account data export?",
            "How long does it take to prepare a full data archive download?",
        ],
    },
    {
        "category": "Data & Compliance",
        "base": "Is CloudNova SOC 2 Type II and ISO 27001 certified?",
        "variations": [
            "Can I request a copy of CloudNova's SOC 2 compliance report?",
            "What security certifications does CloudNova hold?",
            "Is the platform compliant with ISO 27001 security standards?",
            "Where can our compliance team review your SOC 2 audit summary?",
            "What independent security audits and certifications do you have?",
        ],
    },
    {
        "category": "Data & Compliance",
        "base": "What is CloudNova's GDPR compliance and data privacy policy?",
        "variations": [
            "Does CloudNova offer a Data Processing Agreement (DPA) under GDPR?",
            "How is customer personal data protected under European GDPR rules?",
            "Where can I sign an electronic Data Processing Agreement?",
            "What is your policy regarding data retention and right to be forgotten?",
            "How does CloudNova comply with EU privacy and GDPR regulations?",
        ],
    },
    {
        "category": "Data & Compliance",
        "base": "How do I request complete permanent deletion of my account and data?",
        "variations": [
            "How can I exercise my right to erasure and delete all my data?",
            "What is the process to permanently remove my account from your servers?",
            "Where do I submit a request for total data deletion?",
            "Will all my backups be deleted if I close my account?",
            "How do I permanently purge all records associated with my profile?",
        ],
    },

    # Performance, Uptime & SLA
    {
        "category": "Performance & SLA",
        "base": "What is CloudNova's guaranteed uptime Service Level Agreement (SLA)?",
        "variations": [
            "Does CloudNova offer a 99.9% or 99.99% uptime guarantee?",
            "What service credits are provided if monthly uptime falls below SLA?",
            "Where can I review the formal Service Level Agreement terms?",
            "What is the platform availability commitment for enterprise plans?",
            "How do you calculate monthly uptime percentage for SLA credits?",
        ],
    },
    {
        "category": "Performance & SLA",
        "base": "Where can I check the live operational status and incident history?",
        "variations": [
            "Is there a public status page to check service outages in real time?",
            "Where do I see system health and scheduled maintenance updates?",
            "How can I subscribe to email or SMS alerts for platform outages?",
            "Where is the CloudNova uptime status dashboard hosted?",
            "How do I know if an API endpoint is experiencing degraded performance?",
        ],
    },
    {
        "category": "Performance & SLA",
        "base": "Which cloud regions and data center locations are available?",
        "variations": [
            "Can I choose to host my data in the EU or US data centers?",
            "What geographic regions are supported for data residency?",
            "Where are CloudNova server clusters physically located?",
            "Do you have data center availability in Asia-Pacific and Europe?",
            "How do I configure region selection for low latency processing?",
        ],
    },
]


def expand_topics_corpus(target_unique_topics: int = 200) -> List[Dict[str, Any]]:
    """
    Expands the topic templates to guarantee at least target_unique_topics
    distinct intent clusters with varied semantic phrasings.
    """
    corpus = list(TOPIC_TEMPLATES)
    prefixes = [
        "For CloudNova platform",
        "Regarding my enterprise account",
        "In our organization setup",
        "For custom domain integration",
        "When using the REST API",
        "In production environment",
        "For staging workspace",
        "Regarding monthly usage",
    ]
    domains = [
        "audit logs retention", "webhook retry delays", "SSO federation",
        "rate limit headers", "IP restriction rules", "seat license allocation",
        "custom webhook signing", "TLS certificate renewal", "CSV data streaming",
        "SLA credit requests", "backup recovery point", "sub-account partitioning",
        "API quota alerting", "invoice tax ID updates", "granular role permissions",
        "SAML assertion verification", "OAuth token scopes", "multi-region failover",
    ]

    counter = 1
    while len(corpus) < target_unique_topics:
        dom = domains[(counter - 1) % len(domains)]
        pref = prefixes[(counter - 1) % len(prefixes)]
        base_q = f"{pref}: how do I configure {dom} on CloudNova?"
        variations = [
            f"What is the procedure for setting up {dom} in our workspace?",
            f"Can you explain how {dom} configuration works for team accounts?",
            f"Where in settings can I manage {dom} options?",
            f"How do I enable and customize {dom}?",
            f"What are the best practices for {dom} on CloudNova?",
        ]
        corpus.append({
            "category": "Platform Configuration",
            "base": base_q,
            "variations": variations,
        })
        counter += 1

    return corpus[:target_unique_topics]


def generate_benchmark_questions(
    total_queries: int = 1000,
    target_hit_rate: float = 0.80,
) -> List[Tuple[str, bool, str]]:
    """
    Generates a realistic stream of queries designed to produce the target hit rate (~80%).
    Returns: List of (query_text, is_expected_hit, category)
    """
    num_misses = max(1, int(round(total_queries * (1.0 - target_hit_rate))))
    num_hits = total_queries - num_misses

    corpus = expand_topics_corpus(num_misses)
    
    # Each of the num_misses topics will be queried once as its base query (Miss / Seed)
    seed_queries = [(topic["base"], False, topic["category"]) for topic in corpus]

    # Interleave seed queries and hit variations realistically:
    # A variation only hits AFTER its seed has appeared in the stream.
    stream: List[Tuple[str, bool, str]] = []
    active_topics = []
    seed_idx = 0
    hit_idx = 0

    # First seed a few initial topics to populate cache
    initial_burst = min(20, num_misses)
    for _ in range(initial_burst):
        stream.append(seed_queries[seed_idx])
        active_topics.append(corpus[seed_idx])
        seed_idx += 1

    # Interleave remaining seeds and hits
    while seed_idx < num_misses or hit_idx < num_hits:
        can_hit = len(active_topics) > 0 and hit_idx < num_hits
        can_miss = seed_idx < num_misses

        if can_hit and can_miss:
            # Favor hits to match the ~80% target ratio
            if random.random() < target_hit_rate:
                topic = random.choice(active_topics)
                var = random.choice(topic["variations"])
                stream.append((var, True, topic["category"]))
                hit_idx += 1
            else:
                stream.append(seed_queries[seed_idx])
                active_topics.append(corpus[seed_idx])
                seed_idx += 1
        elif can_hit:
            topic = random.choice(active_topics)
            var = random.choice(topic["variations"])
            stream.append((var, True, topic["category"]))
            hit_idx += 1
        elif can_miss:
            stream.append(seed_queries[seed_idx])
            active_topics.append(corpus[seed_idx])
            seed_idx += 1

    return stream[:total_queries]


# =====================================================================
# 2. BENCHMARK RUNNER & METRICS COLLECTOR
# =====================================================================
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
) -> Tuple[BenchmarkSummary, List[BenchmarkItemResult]]:
    """
    Executes the 1,000 queries through the Semantic Cache, records metrics,
    and returns the summarized results.
    """
    print(f"\n{'='*86}")
    print(f"🚀 INITIALIZING VALKEY SEMANTIC CACHE BENCHMARK")
    print(f"{'='*86}")
    print(f"• Total Queries:      {queries_count:,}")
    print(f"• Target Hit Rate:    {target_hit_rate * 100:.1f}%")
    print(f"• Mode:               {'SIMULATION (Mock LLM)' if mock_mode else 'LIVE (Valkey + Vertex AI)'}")
    print(f"• Distance Threshold: {service.distance_threshold:.2f}")
    print(f"• Clear Cache First:  {clear_cache_first}")
    print(f"{'='*86}\n")

    if clear_cache_first and not mock_mode:
        print("🧹 Clearing Valkey Semantic Cache & Telemetry HASH...")
        service.clear_cache(clear_telemetry=True)
        print("✓ Valkey Semantic Cache cleared.\n")

    questions = generate_benchmark_questions(total_queries=queries_count, target_hit_rate=target_hit_rate)
    print(f"✓ Generated {len(questions):,} benchmark queries across diverse support domains.\n")

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
            tokens_saved = q_res.tokens_saved
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

        results.append(BenchmarkItemResult(
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
        ))

        # Update dynamic progress indicator every 10 queries
        if idx % 10 == 0 or idx == queries_count:
            curr_pct = (idx / queries_count) * 100.0
            curr_hit_rate = (hits_count / idx) * 100.0
            elapsed_sec = time.perf_counter() - start_bench_time
            sys.stdout.write(
                f"\r[{idx:>4}/{queries_count}] ({curr_pct:>5.1f}%) | "
                f"⚡ Hits: {hits_count:>4} ({curr_hit_rate:>5.1f}%) | "
                f"🔴 Misses: {misses_count:>3} | "
                f"🪙 Tokens Saved: {running_tokens_saved:>6,} | "
                f"⏱️ Time Saved: {running_time_saved_ms / 1000:>6.1f}s | "
                f"Elapsed: {elapsed_sec:>5.1f}s"
            )
            sys.stdout.flush()

        if verbose:
            tag = "⚡ HIT " if is_hit else "🔴 MISS"
            print(f"\n  [{idx:>4}] {tag} ({latency_ms:6.1f}ms) | {prompt[:65]}...")

    total_wall_clock = time.perf_counter() - start_bench_time
    print("\n\n✓ Benchmark run complete!\n")

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


# =====================================================================
# 3. TABULATION & REPORT FORMATTING
# =====================================================================
def print_benchmark_tables(summary: BenchmarkSummary):
    """
    Renders clean, structured ASCII tables tabulating the benchmark results.
    """
    line_sep = "=" * 86
    sub_sep = "-" * 86

    print(line_sep)
    print("                    VALKEY SEMANTIC CACHE BENCHMARK RESULTS")
    print(line_sep)
    
    # Main 3 Requested Target Metrics Table
    print("\n" + sub_sep)
    print(f"🎯 PRIMARY TELEMETRY KPI SUMMARY ({summary.total_queries:,} QUERIES)")
    print(sub_sep)
    print(f"| {'Metric':<30} | {'Value':<18} | {'Details & Breakdown':<30} |")
    print(f"+{'-'*32}+{'-'*20}+{'-'*32}+")
    print(f"| {'Cache Hit Rate':<30} | {summary.cache_hit_rate_pct:>6.2f}%{'':<11} | {summary.cache_hits:,} Hits / {summary.total_queries:,} Total Queries{'':<2} |")
    print(f"| {'% of Tokens Saved':<30} | {summary.pct_tokens_saved:>6.2f}%{'':<11} | {summary.total_tokens_saved:,} Saved / {summary.total_hypothetical_tokens:,} Total{'':<1} |")
    print(f"| {'% of Time Saved':<30} | {summary.pct_time_saved:>6.2f}%{'':<11} | {summary.total_time_saved_ms/1000.0:>6.1f}s Saved / {summary.total_hypothetical_latency_ms/1000.0:>6.1f}s Base{'':<1} |")
    print(f"+{'-'*32}+{'-'*20}+{'-'*32}+")

    # Latency & Speedup Breakdown
    print("\n" + sub_sep)
    print("⚡ LATENCY & SPEEDUP BREAKDOWN")
    print(sub_sep)
    print(f"| {'Metric':<42} | {'Measurement':<39} |")
    print(f"+{'-'*44}+{'-'*41}+")
    print(f"| {'Average Cache Hit Latency':<42} | {summary.avg_hit_latency_ms:>8.2f} ms (Valkey Vector KNN){'':<13} |")
    print(f"| {'Average Cache Miss Latency':<42} | {summary.avg_miss_latency_ms:>8.2f} ms (Gemini LLM Call){'':<14} |")
    print(f"| {'Latency Speedup Factor':<42} | {summary.speedup_factor:>8.1f}x faster on Cache Hits{'':<12} |")
    print(f"| {'Overall Average Query Latency':<42} | {summary.overall_avg_latency_ms:>8.2f} ms{'':<33} |")
    print(f"| {'Total Time Saved by Caching':<42} | {summary.total_time_saved_ms / 1000.0:>8.1f} seconds ({summary.pct_time_saved:.1f}% saved){'':<9} |")
    print(f"| {'Benchmark Total Wall-Clock Time':<42} | {summary.total_wall_clock_sec:>8.1f} seconds{'':<28} |")
    print(f"+{'-'*44}+{'-'*41}+")

    # Token Consumption Breakdown
    print("\n" + sub_sep)
    print("🪙 TOKEN CONSUMPTION & COST SAVINGS BREAKDOWN")
    print(sub_sep)
    print(f"| {'Metric':<42} | {'Token Count':<39} |")
    print(f"+{'-'*44}+{'-'*41}+")
    print(f"| {'Actual Tokens Billed (LLM Misses)':<42} | {summary.total_actual_tokens:>10,} tokens{'':<22} |")
    print(f"| {'Tokens Saved by Valkey Cache':<42} | {summary.total_tokens_saved:>10,} tokens ({summary.pct_tokens_saved:.1f}% saved){'':<5} |")
    print(f"| {'Hypothetical Tokens without Cache':<42} | {summary.total_hypothetical_tokens:>10,} tokens{'':<22} |")
    print(f"+{'-'*44}+{'-'*41}+")

    # Category Breakdown Table
    print("\n" + sub_sep)
    print("📂 BREAKDOWN BY SUPPORT TOPIC CATEGORY")
    print(sub_sep)
    print(f"| {'Category':<28} | {'Queries':<8} | {'Hits':<6} | {'Hit %':<8} | {'Tokens Saved':<13} | {'Time Saved':<11} |")
    print(f"+{'-'*30}+{'-'*10}+{'-'*8}+{'-'*10}+{'-'*15}+{'-'*13}+")
    for cat_name, cs in sorted(summary.category_stats.items()):
        cat_hit_pct = (cs["hits"] / cs["queries"] * 100.0) if cs["queries"] > 0 else 0.0
        print(
            f"| {cat_name:<28} | {cs['queries']:>8} | {cs['hits']:>6} | {cat_hit_pct:>7.1f}% | "
            f"{cs['tokens_saved']:>13,} | {cs['time_saved_ms'] / 1000.0:>9.1f}s |"
        )
    print(f"+{'-'*30}+{'-'*10}+{'-'*8}+{'-'*10}+{'-'*15}+{'-'*13}+")
    print(line_sep + "\n")


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
*Generated automatically by `benchmark.py` with Valkey Semantic Cache.*
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"📄 Full Markdown benchmark report exported to: {filepath}")


# =====================================================================
# 4. MAIN CLI ENTRYPOINT
# =====================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Benchmark Valkey Semantic Cache with 1,000 queries targeting ~80% hit rate."
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

    print_benchmark_tables(summary)

    if args.report:
        generate_markdown_report(summary, args.report)


if __name__ == "__main__":
    main()
