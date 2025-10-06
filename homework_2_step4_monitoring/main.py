import uvicorn
import asyncio
import threading
from src.monitor import main_monitor # Импортируем функцию запуска монитора

def start_api():
    """Запуск FastAPI сервиса в отдельном потоке."""
    print("🚀 Запуск ONNX Image Captioning Service")
    print("📡 Сервис будет доступен по адресу: http://localhost:8000")
    print("📚 Документация API: http://localhost:8000/docs")
    print("🔍 Health check: http://localhost:8000/health")

    # uvicorn.run блокирует поток, поэтому запускаем его в потоке
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=False, log_level="info")

def start_monitor():
    """Запуск мониторинга в отдельном потоке/event loop."""
    print("\n🔬 Запуск сервиса мониторинга...")
    # asyncio.run() создает новый event loop, что удобно для запуска в потоке
    asyncio.run(main_monitor())


def main():
    """Основная функция для запуска API и Монитора."""
    # Создаем и запускаем поток для FastAPI
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()

    # Запускаем монитор в основном потоке (или в его собственном, как сделано выше)
    # Запуск монитора в отдельном потоке, чтобы не блокировать uvicorn (хотя uvicorn теперь в своем потоке)
    monitor_thread = threading.Thread(target=start_monitor, daemon=True)
    monitor_thread.start()
    
    # Чтобы main не завершился сразу, держим основной поток
    # Можно использовать time.sleep(большое_число) или join
    try:
        while True:
            import time
            time.sleep(1) 
    except KeyboardInterrupt:
        print("\n👋 Сервисы остановлены.")


if __name__ == "__main__":
    main()