"""
HealthLoom Configuration Module
Manages all environment variables and application settings with validation
"""

from typing import List
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings with environment variable validation
    Uses Pydantic for type safety and automatic validation
    """
    
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ==============================================
    # DATABASE CONFIGURATION
    # ==============================================
    database_url: str = Field(
        default="postgresql://healthloom:healthloom@localhost:5432/healthloom",
        description="PostgreSQL connection string"
    )
    db_password: str = Field(
        default="healthloom",
        description="Database password"
    )
    
    # ==============================================
    # AI & ML SERVICES
    # ==============================================
    gemini_api_key: str = Field(
        ...,  # Required field
        description="Google Gemini API key"
    )
    gemini_model: str = Field(
        default="gemini-2.0-flash-exp",
        description="Gemini model name"
    )
    gemini_max_tokens: int = Field(
        default=8192,
        ge=1024,
        le=65536,
        description="Maximum tokens for Gemini responses"
    )
    gemini_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for Gemini generation"
    )
    
    # ==============================================
    # OBSERVABILITY
    # ==============================================
    langfuse_enabled: bool = Field(
        default=False,
        description="Enable LangFuse tracing"
    )
    langfuse_public_key: str = Field(
        default="",
        description="LangFuse public key"
    )
    langfuse_secret_key: str = Field(
        default="",
        description="LangFuse secret key"
    )
    langfuse_host: str = Field(
        default="https://cloud.langfuse.com",
        description="LangFuse host URL"
    )
    
    # ==============================================
    # MEDICATION API (Future Integration)
    # ==============================================
    medication_api_key: str = Field(
        default="",
        description="Medication database API key (to be configured)"
    )
    medication_api_url: str = Field(
        default="",
        description="Medication database API URL (to be configured)"
    )
    
    # ==============================================
    # APPLICATION SETTINGS
    # ==============================================
    environment: str = Field(
        default="development",
        description="Application environment"
    )
    api_host: str = Field(
        default="0.0.0.0",
        description="API host"
    )
    api_port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        description="API port"
    )
    api_reload: bool = Field(
        default=True,
        description="Enable auto-reload in development"
    )
    
    # CORS Settings
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        description="Allowed CORS origins (comma-separated)"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into a list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    # File Upload Settings
    max_upload_size_mb: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum upload size in MB"
    )
    allowed_file_types: str = Field(
        default="image/jpeg,image/png,image/jpg,application/pdf",
        description="Allowed file MIME types (comma-separated)"
    )
    
    @property
    def allowed_file_types_list(self) -> List[str]:
        """Parse allowed file types into a list"""
        return [ft.strip() for ft in self.allowed_file_types.split(",")]
    
    @property
    def max_upload_size_bytes(self) -> int:
        """Convert MB to bytes"""
        return self.max_upload_size_mb * 1024 * 1024
    
    # ==============================================
    # SECURITY SETTINGS
    # ==============================================
    secret_key: str = Field(
        default="development-secret-key-change-in-production",
        min_length=32,
        description="Secret key for session management"
    )
    session_expiration_minutes: int = Field(
        default=1440,  # 24 hours
        ge=30,
        description="Session expiration time in minutes"
    )
    
    # ==============================================
    # LOGGING
    # ==============================================
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    log_format: str = Field(
        default="json",
        description="Log format (json or text)"
    )
    
    # ==============================================
    # PATHS
    # ==============================================
    @property
    def base_dir(self) -> Path:
        """Base directory of the application"""
        return Path(__file__).parent
    
    @property
    def upload_dir(self) -> Path:
        """Directory for uploaded files"""
        path = self.base_dir / "uploads"
        path.mkdir(exist_ok=True)
        return path
    
    @property
    def logs_dir(self) -> Path:
        """Directory for log files"""
        path = self.base_dir / "logs"
        path.mkdir(exist_ok=True)
        return path
    
    # ==============================================
    # VALIDATORS
    # ==============================================
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment value"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v
    
    @validator("gemini_api_key")
    def validate_gemini_api_key(cls, v):
        """Ensure Gemini API key is provided"""
        if not v or v == "your_gemini_api_key_here":
            raise ValueError(
                "GEMINI_API_KEY is required. "
                "Get your key from https://makersuite.google.com/app/apikey"
            )
        return v
    
    # ==============================================
    # HELPER METHODS
    # ==============================================
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"
    
    def get_database_url_sync(self) -> str:
        """Get synchronous database URL (for Alembic)"""
        return self.database_url.replace("postgresql://", "postgresql+psycopg2://")
    
    def get_database_url_async(self) -> str:
        """Get async database URL (for SQLAlchemy async)"""
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://")


# Singleton instance
settings = Settings()


# Validate critical settings on import
def validate_settings():
    """Validate critical settings at startup"""
    errors = []
    
    # Check Gemini API key
    if not settings.gemini_api_key or settings.gemini_api_key == "your_gemini_api_key_here":
        errors.append("GEMINI_API_KEY must be set in .env file")
    
    # Check database URL
    if "your_secure_password_here" in settings.database_url:
        errors.append("DATABASE_URL must be configured with actual password")
    
    # Warn about LangFuse
    if not settings.langfuse_enabled:
        print("⚠️  LangFuse observability is disabled. Enable it for better debugging.")
    
    # Check secret key in production
    if settings.is_production and settings.secret_key == "development-secret-key-change-in-production":
        errors.append("SECRET_KEY must be changed in production environment")
    
    if errors:
        error_msg = "\n".join(f"  ❌ {error}" for error in errors)
        raise ValueError(f"\n\n🚨 Configuration Errors:\n{error_msg}\n")


# Run validation on import (only in non-test environments)
if os.getenv("TESTING") != "true":
    try:
        validate_settings()
        print("[OK] Configuration validated successfully")
    except ValueError as e:
        try:
            print(e)
        except UnicodeEncodeError:
            print(str(e).encode('ascii', 'replace').decode('ascii'))
        print("\nTip: Copy .env.example to .env and fill in your values\n")
        # Don't exit in development to allow config fixes
        if settings.is_production:
            exit(1)
