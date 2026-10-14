from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Agent for Health Insurance Claim Assistance"
    database_url: str = "sqlite:///./claims.db"
    secret_key: str = "change-this-secret-key"

    class Config:
        env_file = ".env"


settings = Settings()
