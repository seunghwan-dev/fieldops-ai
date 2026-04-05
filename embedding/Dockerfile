FROM python:3.11-slim

WORKDIR /app

# WHY: Standalone embedding server for multilingual-e5-large.
#      Separated from backend for independent VRAM management.
# RISK: First model download ~2.5GB. start_period=30s handles delay.
# INTERVIEW: "Isolated embedding service allows fine-grained VRAM allocation."

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    fastapi==0.115.* \
    uvicorn[standard]==0.34.* \
    sentence-transformers==3.3.* \
    torch==2.5.*

COPY server.py .

EXPOSE 8001

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
