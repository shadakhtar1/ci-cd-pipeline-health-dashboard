import pytest

from app.database.init_db import initialize_database
from app.database.session import engine


@pytest.fixture(autouse=True)
def initialize_test_database() -> None:
    """Create SQLAlchemy tables before tests that interact with the database."""
    initialize_database(engine)
