[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "${PROJECT_SLUG}-backend"
version = "${PROJECT_VERSION}"
requires-python = ">=${PYTHON_VERSION}"
dependencies = [
  "asyncpg>=0.30,<1",
  "fastapi>=0.115,<1",
  "pydantic-settings>=2.7,<3",
  "redis>=5,<6",
  "sqlalchemy[asyncio]>=2,<3",
  "uvicorn[standard]>=0.34,<1",
]

[project.optional-dependencies]
dev = ["httpx>=0.28,<1", "pytest>=8,<9", "pytest-asyncio>=0.25,<1", "ruff>=0.9,<1"]

[tool.hatch.build.targets.wheel]
packages = ["app"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100

