from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Settings
    app_name: str = "StudyHub API"
    environment: str = "dev"
    
    # Database Settings
    database_url: str = "postgresql://postgres:password@localhost:5432/studyhub"
    
    # AWS Settings
    aws_region: str = "us-east-1"
    s3_bucket_name: str = "studyhub-materials"
    
    # OpenSearch Settings
    opensearch_endpoint: str = "http://localhost:9200"

    # JWT Authentication
    secret_key: str = "insecure_default_secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # AI Summarization
    summarize_min_paragraph_chars: int = 100
    summarize_max_paragraph_chars: int = 2000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached instance of the settings object.
    """
    return Settings()
