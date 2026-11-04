from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, FetchedValue, Float, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Deteccao(Base):
    """Resultado da classificação de imagem pela IA (gravado pela Function de visão).

    Mapeado desde já para a próxima fase (consulta de detecções); não usado nesta versão.
    """

    __tablename__ = "Deteccoes"

    id: Mapped[int] = mapped_column("Id", Integer, primary_key=True, autoincrement=True)
    estufa_id: Mapped[int | None] = mapped_column("EstufaId", Integer, ForeignKey("Estufas.Id"))
    imagem_blob: Mapped[str] = mapped_column("ImagemBlob", String(400), unique=True)
    classe: Mapped[str] = mapped_column("Classe", String(20))
    confianca: Mapped[Decimal] = mapped_column("Confianca", Numeric(7, 6))
    prob_bacteriano: Mapped[Decimal | None] = mapped_column("ProbBacteriano", Numeric(7, 6))
    prob_fungico: Mapped[Decimal | None] = mapped_column("ProbFungico", Numeric(7, 6))
    prob_saudavel: Mapped[Decimal | None] = mapped_column("ProbSaudavel", Numeric(7, 6))
    patogeno_detectado: Mapped[bool] = mapped_column("PatogenoDetectado", Boolean)
    alerta: Mapped[bool] = mapped_column("Alerta", Boolean)
    modelo_versao: Mapped[str] = mapped_column("ModeloVersao", String(100))
    tempo_inferencia_ms: Mapped[Decimal] = mapped_column("TempoInferenciaMs", Numeric(9, 3))
    data_hora_deteccao: Mapped[datetime] = mapped_column("DataHoraDeteccao", DateTime)
    data_hora_gravacao: Mapped[datetime] = mapped_column(
        "DataHoraGravacao", DateTime, server_default=FetchedValue()
    )
    bbox_x: Mapped[float | None] = mapped_column("BboxX", Float)
    bbox_y: Mapped[float | None] = mapped_column("BboxY", Float)
    bbox_w: Mapped[float | None] = mapped_column("BboxW", Float)
    bbox_h: Mapped[float | None] = mapped_column("BboxH", Float)
    heatmap_blob: Mapped[str | None] = mapped_column("HeatmapBlob", String(400))
    lido: Mapped[bool | None] = mapped_column("Lido", Boolean)
    resolvido: Mapped[bool | None] = mapped_column("Resolvido", Boolean)
    prob_alface: Mapped[Decimal | None] = mapped_column("ProbAlface", Numeric(7, 6))
    modelo_dominio_versao: Mapped[str | None] = mapped_column("ModeloDominioVersao", String(100))
    tempo_verificacao_ms: Mapped[Decimal | None] = mapped_column(
        "TempoVerificacaoMs", Numeric(9, 3)
    )
