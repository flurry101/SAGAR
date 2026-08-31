# attr: m1
# [pytest configuration and test database fixtures]
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.models.user import User  # noqa: F401
from app.main import app

# [in-memory sqlite test database with static pool for shared memory across connections]
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # [create tables for test session]
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def override_db():
    # [override get_db dependency per test]
    def _get_test_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.pop(get_db, None)
# attr: m1

