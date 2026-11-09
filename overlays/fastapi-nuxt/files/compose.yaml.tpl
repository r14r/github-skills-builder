name: ${PROJECT_SLUG}

services:
  backend:
    build: ./backend
    env_file: .env
    ports:
      - "$${BACKEND_PORT}:8000"
    depends_on:
      database:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 10s
      timeout: 3s
      retries: 10

  frontend:
    build: ./frontend
    env_file: .env
    ports:
      - "$${FRONTEND_PORT}:3000"
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "node", "-e", "fetch('http://localhost:3000').then(r=>{if(!r.ok)process.exit(1)})"]
      interval: 10s
      timeout: 3s
      retries: 10

  database:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: $${POSTGRES_DB}
      POSTGRES_USER: $${POSTGRES_USER}
      POSTGRES_PASSWORD: $${POSTGRES_PASSWORD}
    ports:
      - "$${DATABASE_PORT}:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 3s
      retries: 20

  redis:
    image: redis:7-alpine
    ports:
      - "$${REDIS_PORT}:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 20

volumes:
  postgres-data:
  redis-data:

