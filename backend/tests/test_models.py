from sqlalchemy.orm import configure_mappers

from app.models import LeituraSensor, Usuario, UsuarioEstufa


def test_mappers_configure():
    configure_mappers()


def test_models_use_real_column_names():
    assert LeituraSensor.__table__.c.keys() == [
        "Id",
        "DeviceId",
        "Temperatura",
        "Umidade",
        "DataHoraEnvio",
        "DataHoraGravacao",
        "TempTeto",
        "UmidTeto",
        "IdEstufa",
        "Ventoinhas",
    ]
    assert "SenhaHash" in Usuario.__table__.c
    assert [c.name for c in UsuarioEstufa.__table__.primary_key] == ["UsuarioId", "EstufaId"]
