import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_cors_origins_from_comma_separated_string():
    settings = Settings(cors_origins="http://localhost:5173, https://exemplo.com")
    assert settings.cors_origins == ["http://localhost:5173", "https://exemplo.com"]


def test_production_rejects_default_jwt_secret():
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            database_url="mssql+pyodbc://u:p@h/db",
            jwt_secret="dev-only-change-me",
        )


def test_production_rejects_sqlite():
    with pytest.raises(ValidationError):
        Settings(app_env="production", jwt_secret="x" * 40)


def test_production_accepts_valid_config():
    settings = Settings(
        app_env="production",
        jwt_secret="x" * 40,
        database_url="mssql+pyodbc://u:p@h/db?driver=ODBC+Driver+18+for+SQL+Server",
    )
    assert settings.is_production
