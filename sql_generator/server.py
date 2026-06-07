"""API server for sqlgen.

Exposes a FastAPI endpoint to generate SQL from natural language using the SQLGenerator.
Also serves the built React frontend from ``frontend/dist/`` as static files,
so a single Render web service can host both the API and the SPA from one
origin (no CORS needed in production).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel
except ImportError:
    raise ImportError(
        "Server dependencies missing. Install them with: pip install fastapi uvicorn pydantic"
    )

from .generator import SQLGenerator, SQLGeneratorError

# Repository root: <repo>/sql_generator/server.py -> <repo>
REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"

app = FastAPI(
    title="sqlgen API",
    description="Backend API for translating natural language questions into SQL.",
    version="0.1.0",
)

# Enable CORS so the React frontend can make requests from its development port
# (Vite dev server on :5173) and from any other origin. In production the SPA
# is served from this same FastAPI app, so CORS is a no-op there.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    query: str
    dialect: str = "postgresql"
    explain: bool = False
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    api_key: Optional[str] = None
    provider: str = "anthropic"
    ollama_host: Optional[str] = None


@app.post("/api/generate")
async def generate_sql(request: GenerateRequest):
    """Generate SQL from a natural-language query."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    try:
        # Default the model for Ollama if not provided
        model = request.model
        if request.provider == "ollama" and not model:
            model = "qwen2.5-coder"

        # Initialise the generator
        generator = SQLGenerator(
            provider=request.provider,
            model=model,
            max_tokens=request.max_tokens or 1024,
            api_key=request.api_key,
            ollama_host=request.ollama_host,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        result = generator.generate(
            question=request.query,
            dialect=request.dialect,
            explain=request.explain,
        )
        return {
            "sql": result.sql,
            "explanation": result.explanation,
        }
    except SQLGeneratorError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal Generation Error: {exc}")


@app.get("/api/health")
async def health_check():
    """Verify that the API is running and the Anthropic key is configured."""
    key_exists = bool(os.environ.get("ANTHROPIC_API_KEY"))
    return {
        "status": "healthy",
        "api_key_configured": key_exists,
    }


# --- Static frontend (production) ------------------------------------------
# When the React app has been built (frontend/dist/ exists), serve it from
# the same FastAPI process so a single Render web service hosts both the SPA
# and the API. In dev mode (CLI-only or with `npm run dev` for the frontend),
# this directory won't exist and the mounts are skipped — only /api/* is
# available, which is what the Vite dev server expects.

if FRONTEND_DIST.is_dir():
    # Serve hashed bundles, favicon, etc. The root index.html is handled by
    # the SPA fallback below so client-side route refreshes still work.
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_DIST / "assets"),
        name="assets",
    )

    @app.get("/favicon.svg", include_in_schema=False)
    async def favicon() -> FileResponse:
        return FileResponse(FRONTEND_DIST / "favicon.svg")

    @app.get("/icons.svg", include_in_schema=False)
    async def icons() -> FileResponse:
        return FileResponse(FRONTEND_DIST / "icons.svg")

    @app.get("/", include_in_schema=False)
    async def spa_root() -> FileResponse:
        """Serve the React app's index.html at the site root."""
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        """Catch-all: any non-/api GET that didn't match a static file
        returns index.html so React-style client routing works on refresh.
        """
        # Defense in depth: if a request somehow reaches here with an /api/
        # prefix, 404 rather than serve HTML for an API path.
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    print(
        "[sqlgen] frontend/dist/ not found — serving API only. "
        "Run `npm run build` in frontend/ to enable the web UI.",
        file=sys.stderr,
    )


def main():
    """Entry point to run the API server using uvicorn.

    Honors the following environment variables:
    - ``PORT``: render-provided port (used in production on Render).
    - ``SQLGEN_HOST``: bind address (default ``127.0.0.1``).
    - ``SQLGEN_PORT``: fallback port when ``PORT`` is unset (default ``8000``).
    - ``SQLGEN_DEV``: if ``"true"``, enable uvicorn auto-reload.
    """
    import uvicorn

    host = os.environ.get("SQLGEN_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", os.environ.get("SQLGEN_PORT", "8000")))
    reload = os.environ.get("SQLGEN_DEV", "true").lower() == "true"

    uvicorn.run("sql_generator.server:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
