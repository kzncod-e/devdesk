from app.core.config import Settings


def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@host:5432/db")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    s = Settings()
    assert s.database_url == "postgresql+asyncpg://u:p@host:5432/db"
    assert s.jwt_secret == "test-secret"
    assert s.access_token_minutes == 15
    assert s.refresh_token_days == 7
