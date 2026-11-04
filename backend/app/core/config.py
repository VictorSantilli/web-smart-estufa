"""Configurações da aplicação, lidas de variáveis de ambiente (ou do arquivo .env).

Nenhum segredo tem valor padrão utilizável em produção: a validação no final
deste módulo impede que a aplicação suba em produção com valores de desenvolvimento.
"""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

DEV_JWT_SECRET = "dev-only-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Aplicação
    app_name: str = "Smart Estufa"
    app_env: Literal["development", "test", "production"] = "development"
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    # Swagger em /api/docs. Sem valor definido: ligado fora de produção, desligado em produção.
    enable_docs: bool | None = None
    log_level: str = "INFO"

    # Banco de dados (Azure SQL / SQL Server via pyodbc)
    database_url: SecretStr = SecretStr("sqlite+pysqlite:///:memory:")
    database_pool_size: int = 5
    database_echo: bool = False

    # CORS: lista separada por vírgula. Em produção o frontend é servido pela
    # mesma origem, então normalmente fica vazio.
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)

    # Autenticação (usado a partir da Etapa 3)
    jwt_secret: SecretStr = SecretStr(DEV_JWT_SECRET)
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 7
    password_hash_scheme: Literal["bcrypt", "argon2id"] = "bcrypt"
    login_max_attempts: int = 5
    login_lock_minutes: int = 15
    login_ip_max_per_minute: int = 10
    # Cookie de refresh: Secure é obrigatório em produção (HTTPS). Em dev local (http)
    # o navegador recusaria um cookie Secure, por isso o padrão depende do ambiente.
    cookie_secure: bool | None = None
    # Quantos proxies confiáveis acrescentam o IP do cliente ao X-Forwarded-For.
    # 0: usa o IP da conexão (desenvolvimento). 1: Container Apps (o ingress acrescenta
    # o IP real no fim da lista; entradas anteriores podem ter sido forjadas pelo cliente).
    trusted_proxy_hops: int = Field(default=0, ge=0, le=5)

    # Regras de negócio
    app_timezone: str = "America/Sao_Paulo"
    # DataHoraGravacao é gravada pelo DEFAULT do banco no horário de Brasília.
    # Nome Windows (usado no T-SQL AT TIME ZONE) e nome IANA (usado no Python).
    db_local_timezone: str = "E. South America Standard Time"
    db_local_timezone_iana: str = "America/Sao_Paulo"
    stale_after_minutes: int = 15
    history_max_days: int = 60
    temp_min: float = 16.0
    temp_warning: float = 25.0
    temp_critical: float = 26.0
    humidity_min: float = 65.0
    humidity_max: float = 85.0

    # Observabilidade (Azure Application Insights). Vazio = desligado.
    applicationinsights_connection_string: SecretStr | None = None

    # Frontend compilado (servido pelo FastAPI em produção)
    frontend_dist_dir: str = "static"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def _check_production(self) -> "Settings":
        if self.app_env == "production":
            secret = self.jwt_secret.get_secret_value()
            if secret == DEV_JWT_SECRET or len(secret) < 32:
                raise ValueError("JWT_SECRET deve ser definido com pelo menos 32 caracteres")
            if self.database_url.get_secret_value().startswith("sqlite"):
                raise ValueError("DATABASE_URL deve apontar para o Azure SQL em produção")
        return self

    @property
    def refresh_cookie_secure(self) -> bool:
        return self.is_production if self.cookie_secure is None else self.cookie_secure

    @property
    def docs_enabled(self) -> bool:
        return not self.is_production if self.enable_docs is None else self.enable_docs

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
