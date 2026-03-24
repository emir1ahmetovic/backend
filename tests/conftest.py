import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _set_test_env():
    import os

    os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
    os.environ["AWS_REGION"] = "us-east-1"
    os.environ["COGNITO_CLIENT_ID"] = "test-client"
    os.environ["COGNITO_USER_POOL_ID"] = "test-pool"
    yield


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    import app.models  # Ensure all ORM models are registered before create_all
    from app.database import engine
    from app.database import Base

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

