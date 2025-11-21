import os
import json
from functools import lru_cache
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings for environment variable loading."""

    # Application settings
    APP_NAME: str = "GWTM API"
    DEBUG: bool = Field(False, env="DEBUG")
    BASE_URL: str = Field("http://localhost:8000", env="BASE_URL")

    # Database settings
    DB_USER: str = Field("treasuremap", env="DB_USER")
    DB_PWD: str = Field("", env="DB_PWD")
    DB_NAME: str = Field("treasuremap_dev", env="DB_NAME")
    DB_HOST: str = Field("localhost", env="DB_HOST")
    DB_PORT: str = Field("5432", env="DB_PORT")

    # Email settings
    MAIL_USERNAME: str = Field("gwtreasuremap@gmail.com", env="MAIL_USERNAME")
    MAIL_DEFAULT_SENDER: str = Field(
        "gwtreasuremap@gmail.com", env="MAIL_DEFAULT_SENDER"
    )
    MAIL_PASSWORD: str = Field("", env="MAIL_PASSWORD")
    MAIL_SERVER: str = Field("", env="MAIL_SERVER")
    MAIL_PORT: int = Field(465, env="MAIL_PORT")
    MAIL_USE_TLS: bool = Field(False, env="MAIL_USE_TLS")
    MAIL_USE_SSL: bool = Field(True, env="MAIL_USE_SSL")

    # Admin settings
    ADMINS: str = Field("gwtreasuremap@gmail.com", env="ADMINS")

    # Security settings
    SECRET_KEY: str = Field(
        default_factory=lambda: os.urandom(16).hex(), env="SECRET_KEY"
    )
    JWT_SECRET_KEY: str = Field(
        default_factory=lambda: os.urandom(16).hex(), env="JWT_SECRET_KEY"
    )
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # External services
    RECAPTCHA_PUBLIC_KEY: str = Field("", env="RECAPTCHA_PUBLIC_KEY")
    RECAPTCHA_PRIVATE_KEY: str = Field("", env="RECAPTCHA_PRIVATE_KEY")
    ZENODO_ACCESS_KEY: str = Field("", env="ZENODO_ACCESS_KEY")

    # AWS settings
    AWS_ACCESS_KEY_ID: str = Field("", env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field("", env="AWS_SECRET_ACCESS_KEY")
    AWS_DEFAULT_REGION: str = Field("us-east-2", env="AWS_DEFAULT_REGION")
    AWS_BUCKET: str = Field("gwtreasuremap", env="AWS_BUCKET")

    # Azure settings
    AZURE_ACCOUNT_NAME: str = Field("", env="AZURE_ACCOUNT_NAME")
    AZURE_ACCOUNT_KEY: str = Field("", env="AZURE_ACCOUNT_KEY")

    # Swift/OpenStack settings
    OS_AUTH_URL: str = Field("", env="OS_AUTH_URL")
    OS_USERNAME: str = Field("", env="OS_USERNAME")
    OS_PASSWORD: str = Field("", env="OS_PASSWORD")
    OS_STORAGE_URL: str = Field("", env="OS_STORAGE_URL")
    OS_CONTAINER_NAME: str = Field("", env="OS_CONTAINER_NAME")
    OS_USER_DOMAIN_NAME: str = Field("Default", env="OS_USER_DOMAIN_NAME")
    OS_PROJECT_DOMAIN_NAME: str = Field("Default", env="OS_PROJECT_DOMAIN_NAME")
    OS_PROJECT_NAME: str = Field("", env="OS_PROJECT_NAME")

    # Storage settings
    STORAGE_BUCKET_SOURCE: str = Field("s3", env="STORAGE_BUCKET_SOURCE")

    # Development settings
    DEVELOPMENT_MODE: bool = Field(False, env="DEVELOPMENT_MODE")
    DEVELOPMENT_STORAGE_DIR: str = Field("./dev_storage", env="DEVELOPMENT_STORAGE_DIR")

    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]

    @field_validator("CORS_ORIGINS", "CORS_METHODS", "CORS_HEADERS", mode="before")
    @classmethod
    def parse_cors_list(cls, v):
        """Parse CORS settings from JSON string or return as-is if already a list."""
        if isinstance(v, str):
            try:
                # Try to parse as JSON array
                return json.loads(v)
            except json.JSONDecodeError:
                # If JSON parsing fails, treat as comma-separated string
                return [item.strip() for item in v.split(",") if item.strip()]
        return v

    # Database URL
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Generate the database URI from component settings."""
        return f"postgresql://{self.DB_USER}:{self.DB_PWD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Admin emails
    @property
    def ADMIN_EMAILS(self) -> list:
        """Convert comma-separated ADMINS string to a list."""
        return [email.strip() for email in self.ADMINS.split(",")]

    class Config:
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings singleton.
    Uses lru_cache to avoid reading env variables on every call.
    """
    return Settings()


# Export the settings instance for easy importing
settings = get_settings()
