from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from contextlib import asynccontextmanager
from client import MCPUSE_CLIENT
import json

import mcp_use

mcp_use.set_debug(1)

with open("../servers-config/config.json") as f:
    config = json.load(f)
    print(f"Config: {config}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for the FastAPI application."""
    client = MCPUSE_CLIENT(config=config)
    try:
        app.state.client = client
        yield
    except Exception as e:
        print(f"Error during lifespan: {e}")
        raise e
    finally:
        await client.client.close_all_sessions()
        print("Client shutdown successfully.")

app = FastAPI(title="MCP Client API", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str
    payload: Dict[str, Any] = {}


@app.post("/query")
async def process_query(request: QueryRequest):
    """Process a query using the MCP client with access token."""
    try:
        # Pass the access token to the process_query method
        result = await app.state.client.process_query(
            query=request.query,
            payload=request.payload
        )
        print(f"Result: {result}")
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app=app, host="0.0.0.0", port=8000, log_level="info")
