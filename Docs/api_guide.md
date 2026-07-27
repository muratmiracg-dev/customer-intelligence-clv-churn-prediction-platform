# FastAPI Scoring Guide

## Start the Service

```bash
uvicorn API.main:app --reload
```

Open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Example Request

Use `API/sample_request.json` as a complete payload example.

```bash
curl -X POST "http://127.0.0.1:8000/score" \
  -H "Content-Type: application/json" \
  --data @API/sample_request.json
```

## Response

The service returns:

- calibrated churn probability;
- churn classification;
- predicted 12-month CLV;
- model versions and decision threshold.

## Production Extensions

A real deployment should add:

- authenticated access;
- centralized secrets;
- request rate limiting;
- model registry and version pinning;
- feature-contract validation;
- structured logs and tracing;
- latency and error monitoring;
- controlled rollback.

