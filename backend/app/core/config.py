from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import List
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "NEEV — National Education Evidence & Verification"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "neev-phase1-super-secret-key-change-in-production-2026-secure-token")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_GRACE_PERIOD_SECONDS: int = 15
    PASSWORD_RESET_EXPIRE_MINUTES: int = 15
    
    # APAAR secret HMAC key for comparison fingerprint (distinct from JWT SECRET_KEY)
    APAAR_FINGERPRINT_KEY: str = os.getenv("APAAR_FINGERPRINT_KEY", "neev-apaar-hmac-fingerprint-salt-key-2026")
    
    # Database: POSTGRESQL ONLY. SQLite is strictly disallowed across dev, test, staging, and prod.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:2006@localhost:5432/neev_dev")
    SYNC_DATABASE_URL: str = os.getenv("SYNC_DATABASE_URL", "postgresql://postgres:2006@localhost:5432/neev_dev")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://neev01.vercel.app",

    ]
    
    # Upload limits
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB limit for Phase 1 CSV rosters

    @model_validator(mode="after")
    def validate_security_configuration(self):
        # Disallow SQLite completely
        for url_name, url_val in [("DATABASE_URL", self.DATABASE_URL), ("SYNC_DATABASE_URL", self.SYNC_DATABASE_URL)]:
            if not url_val:
                raise ValueError(f"Configuration error: {url_name} must be provided.")
            if "sqlite" in url_val.lower():
                raise ValueError(
                    f"Configuration error: SQLite is strictly prohibited for NEEV. "
                    f"{url_name} must be a valid PostgreSQL connection URL."
                )
            if not url_val.startswith("postgresql"):
                raise ValueError(
                    f"Configuration error: {url_name} must use a PostgreSQL dialect (got '{url_val[:15]}...')."
                )

        # Enforce strong secrets in staging and production
        if self.ENVIRONMENT.lower() in ("production", "prod", "staging"):
            if "change-in-production" in self.SECRET_KEY.lower() or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "Production configuration error: SECRET_KEY must be a cryptographically strong secret "
                    "at least 32 characters long and must not use development placeholders."
                )
            if "salt-key" in self.APAAR_FINGERPRINT_KEY.lower() or len(self.APAAR_FINGERPRINT_KEY) < 24:
                raise ValueError(
                    "Production configuration error: APAAR_FINGERPRINT_KEY must be configured with an explicit "
                    "server-side secret distinct from default placeholders."
                )
        return self

    model_config = SettingsConfigDict(
        env_file=(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"), ".env"),
        extra="allow"
    )

settings = Settings()
