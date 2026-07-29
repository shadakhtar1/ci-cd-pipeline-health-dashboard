from app.database.base import Base
from app.models.build import Build


def initialize_database(engine) -> None:
    """Create all tables for the current metadata.

    This function is intentionally simple and future-ready for migrations.
    """
    Base.metadata.create_all(bind=engine)
