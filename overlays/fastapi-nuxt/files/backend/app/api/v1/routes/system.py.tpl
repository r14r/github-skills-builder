from fastapi import APIRouter

router = APIRouter()


@router.get("/info")
async def info() -> dict[str, str]:
    return {"name": "${PROJECT_NAME}", "version": "${PROJECT_VERSION}"}

