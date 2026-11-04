from unittest.mock import patch

from pydantic import SecretStr

from app.core import telemetry
from app.core.config import Settings


def test_disabled_without_connection_string(monkeypatch):
    monkeypatch.setattr(telemetry, "_configured", False)
    with patch("azure.monitor.opentelemetry.configure_azure_monitor") as configure:
        assert telemetry.configure_telemetry(Settings(_env_file=None)) is False
    configure.assert_not_called()


def test_enabled_once_with_connection_string(monkeypatch):
    monkeypatch.setattr(telemetry, "_configured", False)
    settings = Settings(
        _env_file=None,
        applicationinsights_connection_string=SecretStr("InstrumentationKey=00000000-0000"),
    )
    with patch("azure.monitor.opentelemetry.configure_azure_monitor") as configure:
        assert telemetry.configure_telemetry(settings) is True
        assert telemetry.configure_telemetry(settings) is True
    configure.assert_called_once()
    kwargs = configure.call_args.kwargs
    assert kwargs["connection_string"] == "InstrumentationKey=00000000-0000"
    assert kwargs["logger_name"] == "app"


def test_live_probe_does_not_need_database(client, monkeypatch):
    monkeypatch.setattr("app.api.routes.health.ping_database", lambda: False)
    assert client.get("/api/health/live").json() == {"status": "ok"}
    assert client.get("/api/health").status_code == 503
