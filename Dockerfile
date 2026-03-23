# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/explorer
COPY explorer/package*.json ./
RUN npm ci
COPY explorer/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.12-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY analyst/ ./analyst/
COPY teacher/ ./teacher/
COPY app/ ./app/
COPY integrations/ ./integrations/
COPY serve.py main.py ./

# Copy built frontend
COPY --from=frontend-build /app/explorer/dist ./explorer/dist

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
