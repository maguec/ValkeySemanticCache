"""
Customer Support Corpus Generator for Valkey Semantic Cache Benchmark.
"""

import random
from typing import List, Dict, Any, Tuple

# Comprehensive customer support topic templates and phrasing variations
TOPIC_TEMPLATES: List[Dict[str, Any]] = [
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
