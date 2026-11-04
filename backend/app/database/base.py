from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base dos modelos. As tabelas já existem no Azure SQL: a aplicação nunca
    executa create_all. Mudanças de esquema ficam em database/migrations/."""
