"""API server for sqlgen.

Exposes a FastAPI endpoint to generate SQL from natural language using the SQLGenerator.
"""

from __future__ import annotations

import os
from typing import Optional

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
except ImportError:
    raise ImportError(
        "Server dependencies missing. Install them with: pip install fastapi uvicorn pydantic"
    )

from .generator import SQLGenerator, SQLGeneratorError

app = FastAPI(
    title="sqlgen API",
    description="Backend API for translating natural language questions into SQL.",
    version="0.1.0",
)

# Enable CORS so the React frontend can make requests from its development port
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


def main():
    """Entry point to run the API server using uvicorn."""
    import uvicorn

    host = os.environ.get("SQLGEN_HOST", "127.0.0.1")
    port = int(os.environ.get("SQLGEN_PORT", 8000))
    reload = os.environ.get("SQLGEN_DEV", "true").lower() == "true"

    uvicorn.run("sql_generator.server:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
