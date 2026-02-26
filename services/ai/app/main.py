from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import health

app = FastAPI(title="AI Brokerage — AI Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)


if __name__ == "__main__":
    import uvicorn

    from app.config import settings

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
