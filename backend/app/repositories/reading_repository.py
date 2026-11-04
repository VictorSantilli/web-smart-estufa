"""Consultas de leituras de sensores de UMA estufa.

Uma leitura pertence à estufa quando:
  - LeiturasSensores.IdEstufa é a estufa; ou
  - IdEstufa é nulo e o DeviceId está cadastrado em Dispositivos para a estufa.
Isso cobre as leituras gravadas sem IdEstufa pela Function (regra aprovada na Etapa 1).
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import ColumnElement, Date, and_, func, or_, select
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import FunctionElement

from app.models import Dispositivo, LeituraSensor

L = LeituraSensor


def belongs_to_greenhouse(greenhouse_id: int) -> ColumnElement[bool]:
    devices = select(Dispositivo.device_id).where(Dispositivo.estufa_id == greenhouse_id)
    return or_(
        L.id_estufa == greenhouse_id,
        and_(L.id_estufa.is_(None), L.device_id.in_(devices)),
    )


class ReadingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def latest(self, greenhouse_id: int) -> LeituraSensor | None:
        stmt = (
            select(L)
            .where(belongs_to_greenhouse(greenhouse_id))
            .order_by(L.data_hora_envio.desc(), L.id.desc())
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def latest_with_value(self, greenhouse_id: int, column) -> LeituraSensor | None:
        """Última leitura em que a coluna informada não é nula (último valor válido)."""
        stmt = (
            select(L)
            .where(belongs_to_greenhouse(greenhouse_id), column.is_not(None))
            .order_by(L.data_hora_envio.desc(), L.id.desc())
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def last_recorded_at(self, greenhouse_id: int) -> datetime | None:
        """MAX(DataHoraGravacao), no horário de Brasília (como está no banco)."""
        stmt = select(func.max(L.data_hora_gravacao)).where(belongs_to_greenhouse(greenhouse_id))
        return self.db.scalar(stmt)

    def devices_with_last_contact(
        self, greenhouse_id: int
    ) -> list[tuple[Dispositivo, datetime | None, datetime | None]]:
        """Dispositivos da estufa com MAX(DataHoraEnvio) e MAX(DataHoraGravacao) de cada um."""
        last = (
            select(
                L.device_id.label("device_id"),
                func.max(L.data_hora_envio).label("last_sent"),
                func.max(L.data_hora_gravacao).label("last_recorded"),
            )
            .group_by(L.device_id)
            .subquery()
        )
        stmt = (
            select(Dispositivo, last.c.last_sent, last.c.last_recorded)
            .outerjoin(last, last.c.device_id == Dispositivo.device_id)
            .where(Dispositivo.estufa_id == greenhouse_id)
            .order_by(Dispositivo.device_id)
        )
        return [(d, sent, recorded) for d, sent, recorded in self.db.execute(stmt).all()]


# ---------- histórico ----------


class LocalDate(FunctionElement):
    """Data (dia do calendário) de um DATETIME2 em UTC, no fuso local do projeto.

    - SQL Server: CAST((col AT TIME ZONE 'UTC') AT TIME ZONE '<fuso Windows>' AS date),
      que respeita as regras do fuso (inclusive horário de verão, se voltar a existir).
    - SQLite (apenas nos testes): aplica o deslocamento atual do fuso, em minutos.
    """

    type = Date()
    inherit_cache = True

    def __init__(self, column, windows_tz: str, iana_tz: str) -> None:
        self.windows_tz = windows_tz
        self.iana_tz = iana_tz
        super().__init__(column)


@compiles(LocalDate, "mssql")
def _local_date_mssql(element, compiler, **kw):
    (column,) = element.clauses
    tz = element.windows_tz.replace("'", "''")
    return (
        f"CAST(({compiler.process(column, **kw)} AT TIME ZONE 'UTC') AT TIME ZONE '{tz}' AS date)"
    )


@compiles(LocalDate)
def _local_date_default(element, compiler, **kw):
    (column,) = element.clauses
    offset = datetime.now(ZoneInfo(element.iana_tz)).utcoffset() or timedelta(0)
    minutes = int(offset.total_seconds() // 60)
    return f"date({compiler.process(column, **kw)}, '{minutes:+d} minutes')"


def _deduplicated(greenhouse_id: int, start: datetime, end: datetime):
    """Leituras da estufa no intervalo [start, end) com uma linha por (DeviceId, DataHoraEnvio).

    A fila offline do ESP32 pode reenviar a mesma medição; o par DeviceId + DataHoraEnvio
    identifica a medição. MAX() ignora nulos, então um reenvio com sensor nulo não apaga o valor.
    """
    return (
        select(
            L.device_id.label("device_id"),
            L.data_hora_envio.label("sent_at"),
            func.max(L.temperatura).label("temperature"),
            func.max(L.umidade).label("humidity"),
            func.max(L.temp_teto).label("ceiling_temperature"),
            func.max(L.umid_teto).label("ceiling_humidity"),
        )
        .where(
            belongs_to_greenhouse(greenhouse_id),
            L.data_hora_envio >= start,
            L.data_hora_envio < end,
        )
        .group_by(L.device_id, L.data_hora_envio)
        .subquery("dedup")
    )


HISTORY_SERIES = ("temperature", "humidity", "ceiling_temperature", "ceiling_humidity")


class HistoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def raw(self, greenhouse_id: int, start: datetime, end: datetime):
        d = _deduplicated(greenhouse_id, start, end)
        stmt = select(d).order_by(d.c.sent_at, d.c.device_id)
        return self.db.execute(stmt).mappings().all()

    def daily(
        self, greenhouse_id: int, start: datetime, end: datetime, windows_tz: str, iana_tz: str
    ):
        """Mínimo, média e máximo por dia local de cada série (nulos são ignorados)."""
        d = _deduplicated(greenhouse_id, start, end)
        day = LocalDate(d.c.sent_at, windows_tz, iana_tz)
        columns = [day.label("day"), func.count().label("samples")]
        for name in HISTORY_SERIES:
            col = d.c[name]
            columns += [
                func.min(col).label(f"{name}_min"),
                func.avg(col).label(f"{name}_avg"),
                func.max(col).label(f"{name}_max"),
            ]
        stmt = select(*columns).group_by(day).order_by(day)
        return self.db.execute(stmt).mappings().all()
