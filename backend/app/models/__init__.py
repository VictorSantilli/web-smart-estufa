"""Modelos ORM mapeados para as tabelas existentes do Azure SQL (nomes reais das colunas)."""

from app.models.deteccao import Deteccao
from app.models.dispositivo import Dispositivo
from app.models.estufa import Estufa
from app.models.leitura_sensor import LeituraSensor
from app.models.usuario import Usuario
from app.models.usuario_estufa import UsuarioEstufa

__all__ = ["Deteccao", "Dispositivo", "Estufa", "LeituraSensor", "Usuario", "UsuarioEstufa"]
