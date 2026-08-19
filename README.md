# ⚡ Smart Support Concierge — Valkey Semantic Cache POC

An interactive Proof-of-Concept demonstrating **LangChain's RedisSemanticCache** with a remote **Valkey** server and **Google Cloud Vertex AI (Gemini + text-embedding-004)**. Built with **NiceGUI** and managed with **uv**.

---

## Why Semantic Caching

While caching database results has been a very common way to lower costs and dramatically improve latency, it requires an exact match of the query which works well for templatized queries.  This does not translate well into the world of natural language.

Semantic caching will look at the actual content of the natural language question and search the cache for similar questions.

For example:

- How do I reset my account password?
- How can I recover my credentials?

While obvious to any human that these are the same question by looking at the meaning of the words, this would not work with older methods.  The semantic cache attempts to find questions already answered that are similar.

The caching then can dramatically lower the costs and lantency of serving commonly asked questions.

## When to implement 

You should implement semantic caching if:
- The token cost to answer questions is high
- The latency of those costs is high
- The questions asked are often very similar


You should *NOT* implement semantic caching if:
- The questions being asked are unique - In my experience this is almost never the case despite what most people think.
- Token costs are low and the LLM latency is low


## 🎯 Architecture & How It Works

```
                   +-------------------------------------------------+
                   |           NiceGUI Support Concierge             |
                   |  [ Live Chat ]  [ Telemetry HUD ]  [ Inspector ]|
                   +-------------------------------------------------+
                                           |
                                           v
                          +----------------------------------+
                          |   LangChain RedisSemanticCache   |
                          |  (VertexAIEmbeddings embed_query)|
                          +----------------------------------+
                                   /                \
                    [Cache Hit]   /                  \   [Cache Miss]
                                 v                    v
                       +-------------------+    +--------------------+
                       |   Remote Valkey   |    |  Vertex AI Gemini  |
                       |    (~5-15 ms)     |    |   (~1,200 ms)      |
                       +-------------------+    +--------------------+
```

1. **Semantic Interception**: When a user asks a question, LangChain generates an embedding vector via `text-embedding-004`.
2. **Vector Similarity in Valkey**: It searches the remote Valkey index for cosine similarity against previously cached queries within the configured `distance_threshold` (e.g. `0.20`).
3. **Cache Hit & Sorted Set Leaderboard**: Returns the response in milliseconds with **0 LLM tokens billed**, increments the cache key in a Valkey **Sorted Set (ZSET)** via `ZINCRBY`, and tracks prompt frequency on a live leaderboard by pulling the original prompt from the Valkey **HASH**.
4. **Cache Miss**: Calls Vertex AI Gemini, delivers the response, and vector-stores the prompt-response pair in Valkey.
5. **Persistent Telemetry**: All operational metrics (total queries, hits, misses, tokens saved, latency, speedup) are stored in an atomic Valkey **HASH**, persisting all metrics across application restarts.

---

## 🚀 Getting Started

### 1. Configure Environment Variables (`.env`)

Have a working Valkey server with search enabled.
If you do not have one [this is how to spin one up on Google Cloud](./GCP-Setup.md)

### 2. Configure Environment Variables (`.env`)

Copy `.env.example` to `.env` and fill in your remote Valkey credentials and GCP project:

```bash
# In .env:
VALKEY_URL=redis://:YOUR_REMOTE_PASSWORD@your-valkey-host.example.com:6379/0

# (Or with TLS/SSL if your remote Valkey requires rediss://)
# VALKEY_URL=rediss://:YOUR_REMOTE_PASSWORD@your-valkey-host.example.com:6380/0

GOOGLE_CLOUD_PROJECT=MYPROJECT
GOOGLE_CLOUD_LOCATION=us-west1
VERTEXAI_MODEL=gemini-2.5-flash
VERTEXAI_EMBEDDING_MODEL=text-embedding-004
SEMANTIC_CACHE_DISTANCE_THRESHOLD=0.20
SEMANTIC_CACHE_TTL=3600
```

### 3. Google Cloud Authentication

Ensure you are authenticated to Google Cloud with Application Default Credentials:

```bash
gcloud auth application-default login
```

### 4. Run the NiceGUI Application

Launch the web app with `uv`:

```bash
uv run python main.py
```

> [!TIP]
> **Automatic Index Initialization**: The Python application automatically creates and verifies the vector search index (`support_concierge_cache:support_concierge`) with the exact `TAG` + `NUMERIC` + `VECTOR FLAT` schema on startup—no manual index creation commands or external setup scripts needed.

Open your browser at **`http://localhost:8080`**.

---

## 🧪 Testing the POC

1. Click any **"Base Query (Miss)"** chip under *Quick Semantic Test Variations*:
   - Watch the status show 🔴 **CACHE MISS**, invoking Vertex AI Gemini (~1,200 ms).
   - The query and answer are now stored as a vector embedding in your remote Valkey instance.
2. Click **"Variation 1 (Hit)"** or **"Variation 2 (Hit)"** with alternative phrasing:
   - Notice the instant ⚡ **CACHE HIT** response in **~8 ms** (~120x speedup).
   - Check the **match percentage** (e.g. 94.2% match), the expandable matched source query, and the **Hit counter badge**.
3. Check the **🏆 Top Prompts (Leaderboard)** tab in the right panel:
   - See the most frequently hit prompts dynamically ranked by Valkey **Sorted Set (ZSET)** hit count.
   - Observe how the prompt text and answer preview are retrieved directly from the corresponding Valkey **HASH**.
   - Click the play icon on any leaderboard prompt to immediately re-test that cache hit.
4. Adjust the **Semantic Distance Threshold Slider** live to test strict vs loose matching.
5. Inspect the **Valkey Cache Explorer** tab to view stored keys or purge the cache.
