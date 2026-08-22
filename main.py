import base64
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

# Import our enterprise modules
from schemas import EncodedPayloadRequest, DecodedPayload, SolveResponse
from adapter import V1ToV2Adapter
from metrics import SLOMetricsCalculator

app = FastAPI(title="Adaptive API Gateway V2")

@app.post("/solve", response_model=SolveResponse)
async def solve_gateway_challenge(request: EncodedPayloadRequest):
    try:
        # 1. Decode Base64 string safely
        try:
            decoded_bytes = base64.b64decode(request.payload)
            raw_json_string = decoded_bytes.decode('utf-8')
            parsed_dict = json.loads(raw_json_string)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            raise HTTPException(status_code=400, detail=f"Invalid payload encoding: {str(e)}")

        # 2. Validate the decoded JSON against our strict Pydantic schemas
        try:
            validated_payload = DecodedPayload(**parsed_dict)
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors())

        # 3. Delegate to Domain Services
        adapt_out = V1ToV2Adapter.transform(validated_payload.adaptInput)
        slo_out = SLOMetricsCalculator.calculate(
            heartbeats=validated_payload.heartbeats,
            query=validated_payload.sloQuery
        )

        # 4. Construct and return final validated response
        return SolveResponse(
            adaptOutput=adapt_out,
            sloOutput=slo_out
        )

    except HTTPException:
        raise
    except Exception as e:
        # Catch-all for unexpected server errors (500)
        raise HTTPException(status_code=500, detail=f"Internal Gateway Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Run server programmatically if executed directly
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
