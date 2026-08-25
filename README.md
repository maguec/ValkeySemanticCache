# ⚡ Smart Support Concierge — Valkey Semantic Cache POC

An interactive Proof-of-Concept demonstrating **LangChain's RedisSemanticCache** with a remote **Valkey** (or Memorystore for Valkey) instance and **Google Cloud Vertex AI (Gemini + text-embedding-004)**. Built with **NiceGUI**, containerized with **Docker**, and ready for deployment on **Google Cloud Run**.

---

## Why Semantic Caching

While caching database results has been a very common way to lower costs and dramatically improve latency, it requires an exact match of the query which works well for templatized queries. This does not translate well into the world of natural language.

Semantic caching looks at the actual content of the natural language question and searches the cache for similar questions.

For example:
- *How do I reset my account password?*
- *How can I recover my credentials?*

While obvious to a human that these express the same intent, traditional key-value exact matching misses this. A semantic cache finds previously answered questions that are semantically similar, dramatically lowering costs and latency for serving common questions.

## When to Implement 

You should implement semantic caching if:
- Token costs to answer user queries are high
- LLM response latency is noticeable
- Questions asked by users frequently cover similar topics

You should *NOT* implement semantic caching if:
- The questions being asked are strictly unique per request
- Token costs and LLM latency are negligible

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
3. **Cache Hit & Leaderboard**: Returns the response in milliseconds with **0 LLM tokens billed**, increments the cache key in a Valkey **Sorted Set (ZSET)** via `ZINCRBY`, and tracks prompt frequency on a live leaderboard.
4. **Cache Miss**: Calls Vertex AI Gemini, delivers the response, and vector-stores the prompt-response pair in Valkey.
5. **Persistent Telemetry**: All operational metrics (total queries, hits, misses, tokens saved, latency, speedup) are stored in an atomic Valkey **HASH**, persisting metrics across application restarts.

---

## ⚙️ Environment Variables

The application is configured using the following environment variables:

| Variable | Default | Description |
|---|---|---|
| `VALKEY_URL` | `redis://localhost:6379/0` | Full connection URL (overrides individual host/port) |
| `VALKEY_HOST` | `localhost` | Valkey host IP/hostname |
| `VALKEY_PORT` | `6379` | Valkey port |
| `VALKEY_PASSWORD` | `""` | Valkey authentication password |
| `VALKEY_SSL` | `false` | Enable TLS/SSL connection (`true`/`false`) |
| `GOOGLE_CLOUD_PROJECT` | `mague-tf` | GCP Project ID for Vertex AI |
| `GOOGLE_CLOUD_LOCATION` | `us-central1` | GCP region for Vertex AI models |
| `VERTEXAI_MODEL` | `gemini-2.5-flash` | Gemini model name |
| `VERTEXAI_EMBEDDING_MODEL` | `text-embedding-004` | Vertex AI Embedding model |
| `SEMANTIC_CACHE_DISTANCE_THRESHOLD` | `0.20` | Cosine distance threshold (smaller = stricter) |
| `SEMANTIC_CACHE_TTL` | `3600` | Cache entry expiration in seconds |
| `SEMANTIC_CACHE_INDEX_NAME` | `support_concierge_cache` | Vector index name in Valkey |
| `SEMANTIC_CACHE_PREFIX` | `support_concierge` | Key prefix in Valkey |
| `PORT` | `8080` | Application HTTP listening port |

---

## ☁️ Deploying to Google Cloud Run

Set your target GCP Project ID and Region environment variables before running deployment steps:

```bash
export PROJECT_ID="your-gcp-project-id"
export REGION="your-gcp-region"
```

### Option 1: Using Terraform Templates

The repository includes ready-to-use Terraform modules in the `terraform` folder:

1. **Deploy Application & Infrastructure to Cloud Run**:
   ```bash
   cd ./terraform
   terraform init
   terraform apply \
     -var="gcp_project_id=$PROJECT_ID" \
     -var="region=$REGION" \
     -var="valkey_version=VALKEY_9_0" \
     -var="valkey_mode=CLUSTER_DISABLED" \
     -var="cluster_nodes=1"
   ```

   > [!NOTE]
   > Terraform automatically provisions the VPC network with Direct VPC egress, sets up the Memorystore for Valkey instance, creates the Artifact Registry repository, builds and pushes the **ValkeySemanticCache** source code via Cloud Build, and deploys the application to Cloud Run in `$REGION`.

---

### Option 2: Deploying via `gcloud` CLI

1. **Build and submit the container image to Artifact Registry**:
   ```bash
   gcloud builds submit --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/app/valkey-semantic-cache:latest .
   ```

2. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy valkey-semantic-cache \
     --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/app/valkey-semantic-cache:latest \
     --region ${REGION} \
     --allow-unauthenticated \
     --set-env-vars GOOGLE_CLOUD_PROJECT=${PROJECT_ID} \
     --set-env-vars GOOGLE_CLOUD_LOCATION=${REGION} \
     --set-env-vars VALKEY_URL="redis://:YOUR_PASSWORD@YOUR_VALKEY_IP:6379/0"
   ```

---

## 💻 Local Development

### 1. Configure Local Environment (`.env`)

Copy `.env.example` to `.env` and fill in your Valkey credentials and GCP project:

```bash
cp .env.example .env
```

### 2. Google Cloud Authentication

Authenticate with Google Cloud Application Default Credentials:

```bash
gcloud auth application-default login
```

### 3. Run Locally with `uv`

```bash
uv run python main.py
```

Or run via Docker:

```bash
docker build -t valkey-semantic-cache .
docker run -p 8080:8080 --env-file .env valkey-semantic-cache
```

Open your browser at **`http://localhost:8080`**.

> [!TIP]
> **Automatic Index Initialization**: The application automatically verifies and creates the vector search index (`support_concierge_cache:support_concierge`) with `TAG` + `NUMERIC` + `VECTOR FLAT` schema on startup—no manual schema setup needed.

---

## 🧪 Testing the POC

1. Click any **"Base Query (Miss)"** chip under *Quick Semantic Test Variations*:
   - Status shows 🔴 **CACHE MISS**, invoking Vertex AI Gemini (~1,200 ms).
   - Prompt & answer pair is vectorized and stored in Valkey.
2. Click **"Variation 1 (Hit)"** or **"Variation 2 (Hit)"** with alternative phrasing:
   - Notice the instant ⚡ **CACHE HIT** response in **~8 ms** (~120x speedup).
   - Inspect match percentage, original source query, and hit counters.
3. View the **🏆 Top Prompts (Leaderboard)** tab in the right panel:
   - Live ranking based on Valkey **Sorted Set (ZSET)** hit counts.
4. Adjust the **Semantic Distance Threshold Slider** live to test strict vs loose matching.
5. Inspect the **Valkey Cache Explorer** tab to view stored keys or purge the cache.
