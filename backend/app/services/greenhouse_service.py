from sqlalchemy.orm import Session

from app.models import Usuario
from app.repositories.greenhouse_repository import GreenhouseRepository
from app.schemas.greenhouse import GreenhouseOut, GreenhouseUserOut


class GreenhouseService:
    def __init__(self, db: Session) -> None:
        self.repo = GreenhouseRepository(db)

    def list_for(self, user: Usuario) -> list[GreenhouseOut]:
        items = self.repo.list_all() if user.adm else self.repo.list_for_user(user.id)
        return [GreenhouseOut(id=g.id, name=g.nome) for g in items]

    def users_with_access(self, greenhouse_id: int) -> list[GreenhouseUserOut]:
        return [
            GreenhouseUserOut(
                id=u.id,
                email=u.email,
                name=u.nome,
                is_admin=u.adm,
                is_active=u.ativo,
                linked_at=v.data_vinculo,
            )
            for u, v in self.repo.users_with_access(greenhouse_id)
        ]
