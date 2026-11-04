"""Leitura das imagens das detecções no Azure Blob Storage.

`Deteccoes.ImagemBlob` / `HeatmapBlob` podem guardar a URL completa do blob ou só o caminho.
- URL completa: só é aceita se apontar para a conta configurada em BLOB_ACCOUNT_URL
  (o backend nunca busca um endereço arbitrário vindo do banco).
- Caminho: "<container>/<blob>", ou só "<blob>" quando BLOB_CONTAINER estiver definido.

Autenticação, nesta ordem: BLOB_CONNECTION_STRING (só desenvolvimento), BLOB_SAS_TOKEN
(token só de leitura, para conta de outro diretório), BLOB_ANONYMOUS (container público) e,
por padrão, a identidade gerenciada do Container App (papel "Storage Blob Data Reader").
Nenhuma chave fica no código.
"""

import logging
import mimetypes
from collections.abc import Iterator
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol
from urllib.parse import unquote, urlsplit

from app.core.config import Settings, get_settings
from app.core.errors import AppError

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp"}

STORAGE_NOT_CONFIGURED = AppError(
    503, "storage_not_configured", "O armazenamento de imagens não está configurado."
)
IMAGE_NOT_FOUND = AppError(404, "image_not_found", "Imagem não encontrada.")
STORAGE_UNAVAILABLE = AppError(
    502, "storage_unavailable", "Não foi possível carregar a imagem agora."
)


@dataclass(frozen=True)
class BlobRef:
    container: str
    name: str


@dataclass
class BlobImage:
    chunks: Iterator[bytes]
    content_type: str
    size: int | None
    etag: str | None


class BlobStore(Protocol):
    def open_image(self, ref: str) -> BlobImage: ...


def parse_blob_ref(raw: str, settings: Settings) -> BlobRef:
    """Converte o valor gravado no banco em (container, nome do blob), sem sair da conta."""
    value = (raw or "").strip()
    if not value:
        raise IMAGE_NOT_FOUND
    if value.lower().startswith(("http://", "https://")):
        parts = urlsplit(value)
        account = urlsplit(settings.blob_account_url or "")
        same_account = (
            account.netloc
            and parts.netloc.lower() == account.netloc.lower()
            and parts.scheme == account.scheme
        )
        if not same_account:
            logger.warning("Blob fora da conta configurada ignorado: %s", parts.netloc)
            raise IMAGE_NOT_FOUND
        # Azurite inclui o nome da conta no caminho: http://host:10000/<conta>/<container>/...
        path = parts.path
        if account.path and path.startswith(account.path + "/"):
            path = path[len(account.path) :]
        segments = [unquote(s) for s in path.split("/") if s]
        if len(segments) < 2:
            raise IMAGE_NOT_FOUND
        return _checked(BlobRef(segments[0], "/".join(segments[1:])))
    segments = [s for s in value.split("/") if s]
    if settings.blob_container:
        if segments and segments[0] == settings.blob_container and len(segments) > 1:
            segments = segments[1:]
        return _checked(BlobRef(settings.blob_container, "/".join(segments)))
    if len(segments) < 2:
        raise IMAGE_NOT_FOUND
    return _checked(BlobRef(segments[0], "/".join(segments[1:])))


def _checked(ref: BlobRef) -> BlobRef:
    if not ref.name or ".." in ref.name.split("/"):
        raise IMAGE_NOT_FOUND
    return ref


def _image_type(content_type: str | None, name: str) -> str | None:
    ctype = (content_type or "").split(";")[0].strip().lower()
    # Só deduz pela extensão quando o upload não informou um tipo específico.
    if ctype in ("", "application/octet-stream", "binary/octet-stream"):
        ctype = (mimetypes.guess_type(name)[0] or "").lower()
    return ctype if ctype in ALLOWED_IMAGE_TYPES else None


class AzureBlobStore:
    def __init__(self, settings: Settings) -> None:
        from azure.storage.blob import BlobServiceClient

        self.settings = settings
        conn = settings.blob_connection_string
        if conn is not None:
            self.client = BlobServiceClient.from_connection_string(conn.get_secret_value())
        elif settings.blob_sas_token is not None:
            from azure.core.credentials import AzureSasCredential

            self.client = BlobServiceClient(
                settings.blob_account_url,
                credential=AzureSasCredential(settings.blob_sas_token.get_secret_value()),
            )
        elif settings.blob_anonymous:
            # Container com acesso público de leitura: nenhuma credencial.
            self.client = BlobServiceClient(settings.blob_account_url)
        else:
            from azure.identity import DefaultAzureCredential

            # Em produção usa a identidade gerenciada indicada por AZURE_CLIENT_ID;
            # localmente, o login do `az login`.
            self.client = BlobServiceClient(
                settings.blob_account_url, credential=DefaultAzureCredential()
            )

    def open_image(self, raw: str) -> BlobImage:
        from azure.core.exceptions import AzureError, ResourceNotFoundError

        ref = parse_blob_ref(raw, self.settings)
        blob = self.client.get_blob_client(ref.container, ref.name)
        try:
            props = blob.get_blob_properties()
            ctype = _image_type(props.content_settings.content_type, ref.name)
            if ctype is None:
                logger.warning("Blob sem tipo de imagem permitido: %s/%s", ref.container, ref.name)
                raise IMAGE_NOT_FOUND
            if props.size > self.settings.blob_max_image_mb * 1024 * 1024:
                logger.warning("Imagem acima do limite: %s/%s", ref.container, ref.name)
                raise IMAGE_NOT_FOUND
            downloader = blob.download_blob(etag=props.etag, match_condition=_if_match())
        except ResourceNotFoundError:
            raise IMAGE_NOT_FOUND from None
        except AzureError as exc:
            logger.warning("Falha ao ler o blob: %s: %s", type(exc).__name__, exc)
            raise STORAGE_UNAVAILABLE from None
        return BlobImage(downloader.chunks(), ctype, props.size, props.etag)


def _if_match():
    from azure.core import MatchConditions

    return MatchConditions.IfNotModified


@lru_cache
def _azure_store() -> AzureBlobStore:
    return AzureBlobStore(get_settings())


def get_blob_store() -> BlobStore:
    """Dependência do FastAPI (substituída nos testes)."""
    settings = get_settings()
    if not settings.blob_account_url and settings.blob_connection_string is None:
        raise STORAGE_NOT_CONFIGURED
    return _azure_store()
