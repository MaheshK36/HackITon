"""Small authentication abstraction; production enforcement is environment-configurable."""
from fastapi import Header, HTTPException, status
from backend.config import settings

async def require_write_access(x_api_key: str | None = Header(default=None)) -> None:
    if not settings.require_api_key:
        return
    if not settings.api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Valid X-API-Key required")
