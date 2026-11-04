from datetime import datetime

from sqlalchemy import Boolean, DateTime, FetchedValue, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Dispositivo(Base):
    """Vínculo DeviceId (ESP32) -> estufa. Tabela criada pela migração 001_web_app.sql."""

    __tablename__ = "Dispositivos"

    device_id: Mapped[str] = mapped_column("DeviceId", String(50), primary_key=True)
    estufa_id: Mapped[int] = mapped_column("EstufaId", Integer, ForeignKey("Estufas.Id"))
    descricao: Mapped[str | None] = mapped_column("Descricao", String(100))
    ativo: Mapped[bool] = mapped_column("Ativo", Boolean, server_default=FetchedValue())
    data_criacao: Mapped[datetime] = mapped_column(
        "DataCriacao", DateTime, server_default=FetchedValue()
    )

    estufa: Mapped["Estufa"] = relationship(back_populates="dispositivos")  # noqa: F821
