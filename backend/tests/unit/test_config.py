from app.core.config import Settings


def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@host:5432/db")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    s = Settings()
    assert s.database_url == "postgresql+asyncpg://u:p@host:5432/db"
    assert s.jwt_secret == "test-secret"
    assert s.access_token_minutes == 15
    assert s.refresh_token_days == 7


def test_settings_reads_mongo_env(monkeypatch):
    monkeypatch.setenv("MONGO_URL", "mongodb://somehost:27017")
    monkeypatch.setenv("MONGO_DB_NAME", "otherdb")
    s = Settings()
    assert s.mongo_url == "mongodb://somehost:27017"
    assert s.mongo_db_name == "otherdb"


def test_settings_mongo_defaults():
    s = Settings()
    assert s.mongo_url == "mongodb://localhost:27017"
    assert s.mongo_db_name == "devdesk"
