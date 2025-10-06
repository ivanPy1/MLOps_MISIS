.PHONY: help install start-ollama pull start-pose start-all stop logs-ollama logs-pose test test-agent test-debug-agent test-imports test-ollama-connection test-api notebook clean generate-macarena-gif restart

help:
	@echo "Available commands:"
	@echo "  install               - Install dependencies using Poetry"
	@echo "  start-ollama          - Start Ollama service"
	@echo "  pull                  - Pull qwen2.5:1.5b model (~1GB GGUF)"
	@echo "  start-pose            - Start Pose Visualization service"
	@echo "  start-all             - Start all services (Ollama + Pose API)"
	@echo "  stop                  - Stop all services"
	@echo "  logs-ollama           - Show Ollama service logs"
	@echo "  logs-pose             - Show Pose API service logs"
	@echo "  test                  - Run all tests"
	@echo "  test-agent            - Test the agent with function calling"
	@echo "  test-debug-agent      - Debug test for agent"
	@echo "  test-imports          - Test Python imports"
	@echo "  test-ollama-connection - Test Ollama connection"
	@echo "  test-api              - Test Pose API directly (without LLM)"
	@echo "  notebook              - Start Jupyter notebook"
	@echo "  clean                 - Stop services and clean up"
	@echo "  generate_macarena_gif - Generate Macarena dance GIF"
	@echo "  restart               - Restart all services"

install:
	@echo "Installing dependencies with Poetry..."
	poetry install
	@echo "Dependencies installed!"

start-ollama:
	@echo "Starting Ollama service..."
	docker-compose up -d ollama
	@timeout 5
	@echo "Ollama ready. Now run: make pull"

pull:
	@echo "Pulling qwen2.5:1.5b model (~1GB GGUF)..."
	docker exec ollama_server ollama pull qwen2.5:1.5b
	@echo "Model ready!"

start-pose:
	@echo "Building and starting Pose Visualization service..."
	docker-compose up -d --build pose_api
	@echo "Pose API ready at http://localhost:8001"

start-all:
	@echo "Starting all services..."
	docker-compose up -d --build
	@timeout 5
	@echo "Services ready. Run: make pull"

stop:
	@echo "Stopping all services..."
	docker-compose down
	@echo "Stopped!"

logs-ollama:
	docker-compose logs -f ollama

logs-pose:
	docker-compose logs -f pose_api

test: test-imports test-ollama-connection test-api test-agent
	@echo "All tests completed!"

test-agent:
	@echo "Testing Pose Agent with function calling..."
	poetry run python test_scripts/test_agent.py

test-debug-agent:
	@echo "Debug Test..."
	poetry run python test_scripts/test_debug_agent.py

test-imports:
	@echo "Testing imports..."
	poetry run python test_scripts/test_imports.py

test-ollama-connection:
	@echo "Quick Ollama connection test..."
	poetry run python test_scripts/test_ollama_connection.py

test-api:
	@echo "Testing Pose API..."
	poetry run python test_scripts/test_pose_api.py

notebook:
	@echo "Starting Jupyter notebook..."
	poetry run jupyter notebook

clean: stop
	@echo "Cleaning up..."
	docker-compose down -v
	@echo "Cleanup completed!"

restart: stop start-all
	@echo "Services restarted!"

generate-macarena-gif:
	@echo "Starting to generate a gif with the Macarena dance..."
	poetry run python test_scripts/demo_macarena_direct.py