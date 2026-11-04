from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Estufa, Usuario, UsuarioEstufa


class GreenhouseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, greenhouse_id: int) -> Estufa | None:
        return self.db.get(Estufa, greenhouse_id)

    def list_all(self) -> list[Estufa]:
        return list(self.db.scalars(select(Estufa).order_by(Estufa.id)).all())

    def list_for_user(self, user_id: int) -> list[Estufa]:
        """Somente as estufas vinculadas ao usuário: o filtro é feito no SQL."""
        stmt = (
            select(Estufa)
            .join(UsuarioEstufa, UsuarioEstufa.estufa_id == Estufa.id)
            .where(UsuarioEstufa.usuario_id == user_id)
            .order_by(Estufa.id)
        )
        return list(self.db.scalars(stmt).all())

    def users_with_access(self, greenhouse_id: int) -> list[tuple[Usuario, UsuarioEstufa]]:
        stmt = (
            select(Usuario, UsuarioEstufa)
            .join(UsuarioEstufa, UsuarioEstufa.usuario_id == Usuario.id)
            .where(UsuarioEstufa.estufa_id == greenhouse_id)
            .order_by(Usuario.nome, Usuario.email)
        )
        return [(u, v) for u, v in self.db.execute(stmt).all()]
