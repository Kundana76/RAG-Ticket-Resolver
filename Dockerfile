FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Build the FAISS index at image build time so search uses the real KB
RUN python -m src.build_index
ENV VALKEY_URL=redis://valkey:6379
EXPOSE 8000
CMD ["uvicorn", "copilot.copilot_api:app", "--host", "0.0.0.0", "--port", "8000"]
