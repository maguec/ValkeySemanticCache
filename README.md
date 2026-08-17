# ⚡ Smart Support Concierge — Valkey Semantic Cache POC

An interactive Proof-of-Concept demonstrating **LangChain's RedisSemanticCache** with a remote **Valkey** server and **Google Cloud Vertex AI (Gemini + text-embedding-004)**. Built with **NiceGUI** and managed with **uv**.

---

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
3. **Cache Hit**: Returns the response in milliseconds with **0 LLM tokens billed**.
4. **Cache Miss**: Calls Vertex AI Gemini, delivers the response, and vector-stores the prompt-response pair in Valkey.

---

## 🚀 Getting Started

### 1. Configure Environment Variables (`.env`)

Copy `.env.example` to `.env` and fill in your remote Valkey credentials and GCP project:

```bash
# In .env:
VALKEY_URL=redis://:YOUR_REMOTE_PASSWORD@your-valkey-host.example.com:6379/0

# (Or with TLS/SSL if your remote Valkey requires rediss://)
# VALKEY_URL=rediss://:YOUR_REMOTE_PASSWORD@your-valkey-host.example.com:6380/0

GOOGLE_CLOUD_PROJECT=mague-tf
GOOGLE_CLOUD_LOCATION=us-central1
VERTEXAI_MODEL=gemini-1.5-flash
VERTEXAI_EMBEDDING_MODEL=text-embedding-004
SEMANTIC_CACHE_DISTANCE_THRESHOLD=0.20
SEMANTIC_CACHE_TTL=3600
```

### 2. Google Cloud Authentication

Ensure you are authenticated to Google Cloud with Application Default Credentials:

```bash
gcloud auth application-default login
```

### 3. Run the NiceGUI Application

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
   - Check the **match percentage** (e.g. 94.2% match) and the expandable matched source query.
3. Adjust the **Semantic Distance Threshold Slider** live to test strict vs loose matching.
4. Inspect the **Valkey Cache Explorer** tab to view stored keys or purge the cache.
