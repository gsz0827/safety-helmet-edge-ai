from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Industrial AI Safety Backend"
    app_version: str = "0.1.0"
    app_env: str = "dev"

    edge_config_path: str = "config.yaml"

    database_url: str = "sqlite:///./storage/app.db"

    model_path: str | None = None
    model_input_size: int | None = None
    model_class_names: str | None = None
    detect_conf_threshold: float | None = None
    detect_iou_threshold: float | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )


settings = Settings()
