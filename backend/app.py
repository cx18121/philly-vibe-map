"""FastAPI application with lifespan artifact loading."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.loader import load_artifacts
from backend.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all artifacts into app.state at startup."""
    artifacts = load_artifacts(settings.artifacts_dir)
    for key, value in artifacts.items():
        setattr(app.state, key, value)
    app.state.artifacts_loaded = True
    yield


app = FastAPI(title="Neighbourhood Vibe Mapper API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health():
    """Health check endpoint."""
    loaded = getattr(app.state, "artifacts_loaded", False)
    return {"status": "ok", "artifacts_loaded": loaded}
