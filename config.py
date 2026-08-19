import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file
load_dotenv()


@dataclass
class AppConfig:
    # Valkey / Redis Configuration
    valkey_url: str = os.getenv(
        "VALKEY_URL",
        os.getenv(
            "REDIS_URL",
            "redis://localhost:6379",
        ),
    )
    valkey_host: str = os.getenv("VALKEY_HOST", "localhost")
    valkey_port: int = int(os.getenv("VALKEY_PORT", "6379"))
    valkey_password: str = os.getenv("VALKEY_PASSWORD", "")
    valkey_username: str = os.getenv("VALKEY_USERNAME", "")
    valkey_ssl: bool = os.getenv("VALKEY_SSL", "false").lower() in ("true", "1", "yes")

    # Google Cloud & Vertex AI Configuration
    gcp_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("GCP_PROJECT", "mague-tf"))
    gcp_location: str = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    vertex_model: str = os.getenv("VERTEXAI_MODEL", "gemini-1.5-flash")
    vertex_embedding_model: str = os.getenv("VERTEXAI_EMBEDDING_MODEL", "text-embedding-004")

    # Semantic Cache Settings
    cache_index_name: str = os.getenv("SEMANTIC_CACHE_INDEX_NAME", "support_concierge_cache")
    cache_prefix: str = os.getenv("SEMANTIC_CACHE_PREFIX", "support_concierge")
    cache_leaderboard_key: str = os.getenv("SEMANTIC_CACHE_LEADERBOARD_KEY", "")
    cache_telemetry_key: str = os.getenv("SEMANTIC_CACHE_TELEMETRY_KEY", "")
    distance_threshold: float = float(os.getenv("SEMANTIC_CACHE_DISTANCE_THRESHOLD", "0.20"))
    cache_ttl: int = int(os.getenv("SEMANTIC_CACHE_TTL", "3600"))

    def get_redis_connection_url(self) -> str:
        """Returns normalized Redis / Valkey URL."""
        if self.valkey_url and self.valkey_url != "redis://localhost:6379":
            return self.valkey_url

        # Build URL from components if explicit host/password is provided
        protocol = "rediss" if self.valkey_ssl else "redis"
        auth_part = ""
        if self.valkey_username and self.valkey_password:
            auth_part = f"{self.valkey_username}:{self.valkey_password}@"
        elif self.valkey_password:
            auth_part = f":{self.valkey_password}@"

        return f"{protocol}://{auth_part}{self.valkey_host}:{self.valkey_port}/0"


config = AppConfig()
