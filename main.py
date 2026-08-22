"""
Adaptive API Gateway Challenge - FastAPI Server (Python)
Configured for Uvicorn / FastAPI deployment on Render.
Exposes POST /solve
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from solver import decode_payload, solve_challenge
app = FastAPI(
    title="Adaptive API Gateway",
    description="Adaptive API Gateway Challenge Server"
)
# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Adaptive API Gateway (FastAPI) server running"
    }
@app.post("/solve")
async def solve_endpoint(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    try:
        payload_data = decode_payload(body)
        result = solve_challenge(payload_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Bad Request: {str(e)}")
if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
