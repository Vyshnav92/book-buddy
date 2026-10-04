# syntax=docker/dockerfile:1

# ---------- Stage 1: build the React frontend ----------
FROM node:22-alpine AS frontend-build
WORKDIR /build

# Copy only the dependency files first so Docker can cache "npm ci"
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Now copy the source and build the static files into /build/dist
COPY frontend/ ./
RUN npm run build


# ---------- Stage 2: Flask backend that also serves the built frontend ----------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Same folder layout as the repo: /app/backend and /app/frontend/dist
WORKDIR /app/backend

# Install Python dependencies (gunicorn is the production server)
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy the backend code and the built frontend from stage 1
COPY backend/ ./
COPY --from=frontend-build /build/dist /app/frontend/dist

# Run as a normal user; SQLite lives in the instance folder
RUN useradd --create-home appuser \
    && mkdir -p /app/backend/instance \
    && chown -R appuser:appuser /app/backend/instance
USER appuser

EXPOSE 5000

# Marks the container "healthy" only if the API answers
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/api/health')" || exit 1

# 1 worker + 4 threads (SQLite is happy with that); 60s timeout leaves room for the AI call
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--timeout", "60", "app:app"]
