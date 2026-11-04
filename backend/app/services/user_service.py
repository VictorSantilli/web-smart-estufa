"""Gerenciamento de usuários (somente ADM; a checagem de perfil fica nas rotas)."""

from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.errors import AppError
from app.core.security import hash_password
from app.models import Usuario, UsuarioEstufa
from app.repositories.user_repository import UserRepository
from app.schemas.auth import GreenhouseRef
from app.schemas.common import Page
from app.schemas.user import UserCreate, UserOut, UserUpdate

USER_NOT_FOUND = AppError(404, "user_not_found", "Usuário não encontrado.")
EMAIL_IN_USE = AppError(409, "email_in_use", "Já existe um usuário com este e-mail.")


def to_user_out(user: Usuario) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.nome,
        is_admin=user.adm,
        is_active=user.ativo,
        created_at=user.data_criacao,
        greenhouses=sorted(
            (GreenhouseRef(id=v.estufa.id, name=v.estufa.nome) for v in user.vinculos),
            key=lambda g: g.id,
        ),
    )


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def list_users(
        self, *, search: str | None, active: bool | None, page: int, page_size: int
    ) -> Page[UserOut]:
        items, total = self.users.list_users(
            search=search, active=active, offset=(page - 1) * page_size, limit=page_size
        )
        return Page(
            items=[to_user_out(u) for u in items], total=total, page=page, page_size=page_size
        )

    def get(self, user_id: int) -> UserOut:
        user = self.users.get_with_greenhouses(user_id)
        if user is None:
            raise USER_NOT_FOUND
        return to_user_out(user)

    def create(self, data: UserCreate) -> UserOut:
        email = str(data.email).lower()
        if self.users.get_by_email(email):
            raise EMAIL_IN_USE
        greenhouse_ids = self._validate_greenhouses(set(data.greenhouse_ids))
        user = Usuario(
            email=email,
            nome=data.name,
            senha_hash=hash_password(data.password),
            data_criacao=utcnow(),
            adm=data.is_admin,
            ativo=True,
            tentativas_falhas=0,
            token_versao=0,
        )
        self.users.add(user)
        today = utcnow().date()
        for gid in sorted(greenhouse_ids):
            self.db.add(UsuarioEstufa(usuario_id=user.id, estufa_id=gid, data_vinculo=today))
        self.db.commit()
        return self.get(user.id)

    def update(self, user_id: int, data: UserUpdate, acting_user: Usuario) -> UserOut:
        user = self._get_or_404(user_id)
        if data.email is not None:
            email = str(data.email).lower()
            other = self.users.get_by_email(email)
            if other and other.id != user.id:
                raise EMAIL_IN_USE
            user.email = email
        if data.name is not None:
            user.nome = data.name.strip()
        if data.is_admin is not None:
            if user.id == acting_user.id and not data.is_admin:
                raise AppError(
                    400, "cannot_demote_self", "Você não pode remover seu próprio perfil de ADM."
                )
            if user.adm != data.is_admin:
                user.adm = data.is_admin
                user.token_versao += 1  # perfil mudou: força novo login
        if data.password is not None:
            user.senha_hash = hash_password(data.password)
            user.token_versao += 1  # senha trocada: derruba as sessões abertas
            user.tentativas_falhas = 0
            user.bloqueado_ate = None
        self.db.commit()
        return self.get(user.id)

    def set_active(self, user_id: int, active: bool, acting_user: Usuario) -> UserOut:
        user = self._get_or_404(user_id)
        if not active and user.id == acting_user.id:
            raise AppError(
                400, "cannot_deactivate_self", "Você não pode desativar a própria conta."
            )
        if user.ativo != active:
            user.ativo = active
            if not active:
                user.token_versao += 1
            else:
                user.tentativas_falhas = 0
                user.bloqueado_ate = None
        self.db.commit()
        return self.get(user.id)

    def set_greenhouses(self, user_id: int, greenhouse_ids: list[int]) -> UserOut:
        user = self._get_or_404(user_id)
        wanted = self._validate_greenhouses(set(greenhouse_ids))
        current = self.users.greenhouse_ids(user.id)
        today = utcnow().date()
        for gid in current - wanted:
            self.db.query(UsuarioEstufa).filter_by(usuario_id=user.id, estufa_id=gid).delete()
        for gid in sorted(wanted - current):
            self.db.add(UsuarioEstufa(usuario_id=user.id, estufa_id=gid, data_vinculo=today))
        self.db.commit()
        self.db.expire_all()
        return self.get(user.id)

    def _get_or_404(self, user_id: int) -> Usuario:
        user = self.users.get(user_id)
        if user is None:
            raise USER_NOT_FOUND
        return user

    def _validate_greenhouses(self, ids: set[int]) -> set[int]:
        missing = ids - self.users.existing_greenhouse_ids(ids)
        if missing:
            raise AppError(
                422,
                "greenhouse_not_found",
                f"Estufa(s) inexistente(s): {', '.join(map(str, sorted(missing)))}.",
            )
        return ids
