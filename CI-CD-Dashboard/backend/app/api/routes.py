from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.build import Build
from app.schemas.build import BuildCreate, BuildRead, BuildSummary, RefreshResponse
from app.services.build_service import BuildService

router = APIRouter(prefix="/api", tags=["dashboard"])


def get_build_service(db: Session = Depends(get_db)) -> BuildService:
    return BuildService(db)


@router.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/dashboard", response_model=BuildSummary)
async def get_dashboard(service: BuildService = Depends(get_build_service)) -> BuildSummary:
    return service.get_dashboard_summary()


@router.get("/builds", response_model=list[BuildRead])
async def list_builds(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    service: BuildService = Depends(get_build_service),
) -> list[BuildRead]:
    return service.list_builds(skip=skip, limit=limit)


@router.get("/builds/{build_id}", response_model=BuildRead)
async def get_build(build_id: int, service: BuildService = Depends(get_build_service)) -> BuildRead:
    build = service.get_build(build_id)
    if build is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found")
    return build


@router.get("/builds/{build_id}/logs", response_model=dict[str, str | None])
async def get_build_logs(build_id: int, service: BuildService = Depends(get_build_service)) -> dict[str, str | None]:
    build = service.get_build(build_id)
    if build is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found")
    return {"logs": build.logs}


@router.post("/refresh", response_model=RefreshResponse, status_code=status.HTTP_200_OK)
async def refresh_builds(service: BuildService = Depends(get_build_service)) -> RefreshResponse:
    return service.refresh_builds()
