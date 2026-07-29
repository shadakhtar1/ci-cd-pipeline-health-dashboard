from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models.build import Build


def test_database_can_create_and_query_builds() -> None:
    """The database layer should allow creating and retrieving a build record."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        build = Build(
            pipeline_name="demo-pipeline",
            build_number=42,
            workflow_name="CI",
            status="success",
            duration=120,
            branch="main",
            commit_id="abc123",
            commit_message="Test commit",
            author="tester",
            logs="sample logs",
        )
        session.add(build)
        session.commit()

        saved = session.query(Build).filter(Build.build_number == 42).first()

    assert saved is not None
    assert saved.pipeline_name == "demo-pipeline"
    assert saved.status == "success"
