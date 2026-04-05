FROM python:3.11-slim

WORKDIR /app

# WHY: FieldOps-AI API Gateway built on FastAPI.
# RISK: Oracle Instant Client not available in slim image,
#       but oracledb thin mode eliminates this dependency.
# INTERVIEW: "P1-proven FastAPI + oracledb thin mode — no Instant Client needed."

RUN apt-get update && apt-get install -y --no-install-recommends curl poppler-utils && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    fastapi==0.115.* \
    uvicorn[standard]==0.34.* \
    oracledb==2.5.* \
    httpx==0.28.* \
    python-multipart==0.0.* \
    pydantic-settings==2.7.* \
    openai==1.* \
    pdf2image==1.* \
    scikit-learn==1.6.* \
    joblib==1.* \
    shap==0.46.*

RUN pip install --no-cache-dir pytest==8.* pytest-asyncio==0.24.* httpx==0.28.*

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
