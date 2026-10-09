# Run `make help` for the list of targets.
.DEFAULT_GOAL := help
API_PORT ?= 8000
UI_PORT  ?= 8501

help:  ## Show this help
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------- local (macOS / Linux, no Docker)
setup:  ## Install backend (with model runtime) and frontend environments
	uv sync --project backend --extra ml
	uv sync --project frontend

models:  ## Download model weights into the Hugging Face cache
	uv run --project backend python -m backend.infrastructure.ml.download

api:  ## Run the API on this machine (CUDA, Apple MPS or CPU)
	HF_HUB_OFFLINE=1 PYTORCH_ENABLE_MPS_FALLBACK=1 \
	uv run --project backend uvicorn backend.main:create_app --factory --port $(API_PORT)

ui:  ## Run the Streamlit UI
	PYTHONPATH=. SAWT_API_URL=http://localhost:$(API_PORT) \
	uv run --project frontend streamlit run frontend/app.py --server.port $(UI_PORT)

dev-mac:  ## Apple Silicon: API on the GPU (MPS) + translation via Ollama + UI
	@ollama list | grep -q "$${SAWT_OLLAMA_MODEL:-qwen3:4b-instruct-2507-q4_K_M}" || ollama pull "$${SAWT_OLLAMA_MODEL:-qwen3:4b-instruct-2507-q4_K_M}"
	@trap 'kill 0' EXIT; SAWT_TRANSLATION_BACKEND=ollama $(MAKE) api & $(MAKE) ui

# ---------------------------------------------------------------- Docker
up:  ## Docker, NVIDIA GPU
	docker compose run --rm -e HF_HUB_OFFLINE=0 api python -m backend.infrastructure.ml.download
	docker compose up --build

up-cpu:  ## Docker, CPU only (slow); translation via Ollama on the host
	docker compose -f compose.yaml -f compose.cpu.yaml run --rm -e HF_HUB_OFFLINE=0 api python -m backend.infrastructure.ml.download
	docker compose -f compose.yaml -f compose.cpu.yaml up --build

down:  ## Stop the Docker stack
	docker compose down

# ---------------------------------------------------------------- docs
MMDC = npx -y -p @mermaid-js/mermaid-cli@11 mmdc -q

diagrams:  ## Re-render docs/images/*.svg from docs/diagrams/*.mmd (needs Node.js)
	@for d in overview system pipeline; do \
	  $(MMDC) -c docs/diagrams/theme-light.json -b '#FFFFFF' -i docs/diagrams/$$d.mmd -o docs/images/$$d-light.svg; \
	  $(MMDC) -c docs/diagrams/theme-dark.json -b '#0D1117' -i docs/diagrams/$$d.mmd -o docs/images/$$d-dark.svg; \
	done

# ---------------------------------------------------------------- quality
test:  ## Run all tests (no models needed)
	uv run --project backend pytest backend/tests -q
	uv run --project frontend pytest frontend/tests -q

lint:  ## Lint and check formatting
	uv run --project backend ruff check backend && uv run --project backend ruff format --check backend
	uv run --project frontend ruff check frontend && uv run --project frontend ruff format --check frontend
	uv run --project backend ruff check examples && uv run --project backend ruff format --check examples

format:  ## Auto-format
	uv run --project backend ruff format backend && uv run --project backend ruff check --fix backend
	uv run --project frontend ruff format frontend && uv run --project frontend ruff check --fix frontend
	uv run --project backend ruff format examples && uv run --project backend ruff check --fix examples

.PHONY: help setup models api ui dev-mac up up-cpu down diagrams test lint format
