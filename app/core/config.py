from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    environment: str
    debug: bool
    log_level: str


def load_settings() -> Settings:
    debug_value = getenv("APP_DEBUG", "false").strip().lower()
    debug = debug_value in {"1", "true", "yes", "on"}

    return Settings(
        app_name=getenv("APP_NAME", "Prayer Timing API"),
        app_version=getenv("APP_VERSION", "0.1.0"),
        environment=getenv("APP_ENVIRONMENT", "development"),
        debug=debug,
        log_level=getenv("LOG_LEVEL", "DEBUG" if debug else "INFO").upper(),
    )


settings = load_settings()
