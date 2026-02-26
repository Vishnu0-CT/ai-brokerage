from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request):
    be_ok = False
    try:
        await request.app.state.be_client.health()
        be_ok = True
    except Exception:
        pass

    return {"status": "ok" if be_ok else "degraded", "be_service": be_ok}
