"""Telemetria no Azure Application Insights (OpenTelemetry).

Ligada somente quando APPLICATIONINSIGHTS_CONNECTION_STRING está definida (no Container
Apps ela vem como secret). Envia requisições HTTP, exceções, dependências HTTP e os logs
da aplicação. Cabeçalhos (como Authorization) e corpos de requisição não são enviados.
"""

import logging

from app.core.config import Settings

logger = logging.getLogger(__name__)
_configured = False


def configure_telemetry(settings: Settings) -> bool:
    """Configura o Application Insights uma única vez. Retorna True se ficou ativo."""
    global _configured
    connection_string = settings.applicationinsights_connection_string
    if _configured or connection_string is None:
        return _configured

    from azure.monitor.opentelemetry import configure_azure_monitor
    from opentelemetry.sdk.resources import Resource

    configure_azure_monitor(
        connection_string=connection_string.get_secret_value(),
        # Só os logs da aplicação (namespace "app"), não os de bibliotecas.
        logger_name="app",
        resource=Resource.create(
            {
                "service.name": settings.app_name,
                "service.version": settings.app_version,
                "deployment.environment": settings.app_env,
            }
        ),
        # Instrumentações que o projeto não usa.
        instrumentation_options={
            "django": {"enabled": False},
            "flask": {"enabled": False},
            "psycopg2": {"enabled": False},
        },
    )
    _configured = True
    logger.info("Application Insights ativo")
    return True
