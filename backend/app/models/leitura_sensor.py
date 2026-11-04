from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, FetchedValue, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class LeituraSensor(Base):
    """Leitura gravada pela Azure Function de telemetria (somente leitura para o app web).

    - Temperatura/Umidade: sensor do dossel; TempTeto/UmidTeto: sensor do teto.
    - DataHoraEnvio: hora da medição em UTC (NTP do ESP32). É a hora oficial da leitura.
    - DataHoraGravacao: hora de gravação no horário de Brasília (DEFAULT do banco).
    - IdEstufa pode ser nulo; nesse caso a estufa vem de Dispositivos pelo DeviceId.
    - Valores de sensor podem ser nulos quando o sensor falha.
    """

    __tablename__ = "LeiturasSensores"

    id: Mapped[int] = mapped_column("Id", Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column("DeviceId", String(50))
    temperatura: Mapped[Decimal | None] = mapped_column("Temperatura", Numeric(5, 2))
    umidade: Mapped[Decimal | None] = mapped_column("Umidade", Numeric(5, 2))
    data_hora_envio: Mapped[datetime] = mapped_column("DataHoraEnvio", DateTime)
    data_hora_gravacao: Mapped[datetime | None] = mapped_column(
        "DataHoraGravacao", DateTime, server_default=FetchedValue()
    )
    temp_teto: Mapped[Decimal | None] = mapped_column("TempTeto", Numeric(5, 2))
    umid_teto: Mapped[Decimal | None] = mapped_column("UmidTeto", Numeric(5, 2))
    id_estufa: Mapped[int | None] = mapped_column("IdEstufa", Integer, ForeignKey("Estufas.Id"))
    ventoinhas: Mapped[bool | None] = mapped_column("Ventoinhas", Boolean)
