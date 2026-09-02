import os
from typing import Optional
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "SAGAR API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Documentation configuration (automatically disabled in production unless explicitly overridden)
    DOCS_URL: Optional[str] = None
    REDOC_URL: Optional[str] = None
    OPENAPI_URL: Optional[str] = None

    # CORS configuration
    # Default to the configured frontend URL; allow an explicit override for
    # multiple origins in staging or multi-tenant deployments.
    CORS_ALLOW_ORIGINS: str = ""
    CORS_ALLOW_CREDENTIALS: bool = True

    # Supabase Configuration
    SUPABASE_PROJECT_ID: str = ""
    SUPABASE_JWT_SECRET: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_DB_URL: Optional[str] = None

    # PostgreSQL Connection Parameters
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgrespassword"
    POSTGRES_DB: str = "sagar_db"
    # Explicit Database URL (Takes precedence if provided, e.g. for Supabase PostgreSQL)
    DATABASE_URL: Optional[str] = None

    # Bhashini Translation API
    BHASHINI_API_KEY: str = ""
    BHASHINI_USER_ID: str = ""
    BHASHINI_PIPELINE_URL: str = "https://meity-auth.udyat.ai/ulca/apis/v0/model/getModelsPipeline"

    # Google AI
    GOOGLE_API_KEY: str = ""

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # Frontend URL (for OAuth redirect after callback)
    FRONTEND_URL: str = "http://localhost:5173"

    # WorldTides
    WORLDTIDES_API_KEY: str = ""

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def service_role_key(self) -> str:
        return self.SUPABASE_SERVICE_ROLE_KEY or self.SUPABASE_SERVICE_KEY

    @property
    def cors_allow_origins(self) -> list[str]:
        origins = [
            origin.strip()
            for origin in self.CORS_ALLOW_ORIGINS.split(",")
            if origin.strip()
        ]
        frontend_origin = self.FRONTEND_URL.strip().rstrip("/")
        if frontend_origin and frontend_origin not in origins:
            origins.insert(0, frontend_origin)
        if not self.is_production:
            for local_origin in [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]:
                if local_origin not in origins:
                    origins.append(local_origin)
        return origins

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.strip().lower() in ("production", "prod")

    @property
    def docs_url(self) -> Optional[str]:
        if self.DOCS_URL is not None:
            return self.DOCS_URL
        return None if self.is_production else "/docs"

    @property
    def redoc_url(self) -> Optional[str]:
        if self.REDOC_URL is not None:
            return self.REDOC_URL
        return None if self.is_production else "/redoc"

    @property
    def openapi_url(self) -> Optional[str]:
        if self.OPENAPI_URL is not None:
            return self.OPENAPI_URL
        return None if self.is_production else "/openapi.json"

    model_config = SettingsConfigDict(
        env_file=(
            os.getenv("ENV_FILE", ".env"),
            "../.env",
            ".env",
        ),
        extra="ignore",
    )


settings = Settings()


