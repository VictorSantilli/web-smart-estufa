from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Estufa, Usuario, UsuarioEstufa


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: int) -> Usuario | None:
        return self.db.get(Usuario, user_id)

    def get_with_greenhouses(self, user_id: int) -> Usuario | None:
        stmt = (
            select(Usuario)
            .options(selectinload(Usuario.vinculos).selectinload(UsuarioEstufa.estufa))
            .where(Usuario.id == user_id)
        )
        return self.db.scalars(stmt).first()

    def get_by_email(self, email: str) -> Usuario | None:
        stmt = select(Usuario).where(func.lower(Usuario.email) == email.strip().lower())
        return self.db.scalars(stmt).first()

    def list_users(
        self, *, search: str | None, active: bool | None, offset: int, limit: int
    ) -> tuple[list[Usuario], int]:
        stmt = select(Usuario)
        if search:
            like = f"%{search.strip()}%"
            stmt = stmt.where(or_(Usuario.email.ilike(like), Usuario.nome.ilike(like)))
        if active is not None:
            stmt = stmt.where(Usuario.ativo == active)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = self.db.scalars(
            stmt.options(selectinload(Usuario.vinculos).selectinload(UsuarioEstufa.estufa))
            .order_by(Usuario.nome, Usuario.email)
            .offset(offset)
            .limit(limit)
        ).all()
        return list(items), total

    def add(self, user: Usuario) -> Usuario:
        self.db.add(user)
        self.db.flush()
        return user

    def greenhouse_ids(self, user_id: int) -> set[int]:
        stmt = select(UsuarioEstufa.estufa_id).where(UsuarioEstufa.usuario_id == user_id)
        return set(self.db.scalars(stmt).all())

    def has_greenhouse(self, user_id: int, greenhouse_id: int) -> bool:
        stmt = select(UsuarioEstufa.estufa_id).where(
            UsuarioEstufa.usuario_id == user_id, UsuarioEstufa.estufa_id == greenhouse_id
        )
        return self.db.scalar(stmt) is not None

    def existing_greenhouse_ids(self, ids: set[int]) -> set[int]:
        if not ids:
            return set()
        return set(self.db.scalars(select(Estufa.id).where(Estufa.id.in_(ids))).all())
