import httpx
import asyncio
import requests


class APIClient:
    """Клиент для тестирования FastAPI сервиса"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    async def test_health(self):
        """Проверка health endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            print(f"Health check: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {response.json()}")
            else:
                print(f"Error: {response.text}")
            return response.status_code == 200

    async def download_test_image(self, url: str, filename: str):
        """Загрузка тестового изображения"""
        response = requests.get(url)
        if response.status_code == 200:
            with open(f"test_images/{filename}", "wb") as f:
                f.write(response.content)
            print(f"✅ Загружено тестовое изображение: {filename}")
        else:
            print(f"❌ Ошибка загрузки изображения: {response.status_code}")

    async def test_single_prediction(self, image_path: str):
        """Тестирование инференса одного изображения"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                with open(image_path, "rb") as f:
                    files = {"file": (image_path, f, "image/jpeg")}
                    response = await client.post(
                        f"{self.base_url}/predict", files=files
                    )

                print(f"\n📸 Тест одного изображения: {image_path}")
                print(f"Status: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Успешно обработано: {result['filename']}")
                    print(
                        f"Время инференса: {result['result']['timing']['inference_ms']:.2f} мс"
                    )
                    print(
                        f"Общее время: {result['result']['timing']['total_ms']:.2f} мс"
                    )
                else:
                    print(f"❌ Ошибка: {response.text}")

        except Exception as e:
            print(f"❌ Исключение при тестировании: {e}")

    async def test_batch_prediction(self, image_paths: list):
        """Тестирование batch инференса"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                files = []
                for path in image_paths:
                    with open(path, "rb") as f:
                        files.append(("files", (path, f.read(), "image/jpeg")))

                response = await client.post(
                    f"{self.base_url}/predict_batch", files=files
                )

                print(f"\n📚 Тест batch инференса ({len(image_paths)} изображений)")
                print(f"Status: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    stats = result["batch_stats"]
                    print("✅ Batch обработан успешно")
                    print(f"Размер батча: {stats['batch_size']}")
                    print(f"Общее время батча: {stats['total_batch_time_ms']:.2f} мс")
                    print(
                        f"Среднее время на изображение: {stats['avg_time_per_image_ms']:.2f} мс"
                    )

                    for res in result["results"]:
                        inf_time = res["timing"]["inference_ms"]
                        print(f"  - {res['filename']}: {inf_time:.2f} мс")
                else:
                    print(f"❌ Ошибка: {response.text}")

        except Exception as e:
            print(f"❌ Исключение при batch тестировании: {e}")


async def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование FastAPI сервиса ONNX модели\n")

    client = APIClient()

    is_healthy = await client.test_health()
    if not is_healthy:
        print("❌ Сервис недоступен. Убедитесь что он запущен.")
        return

    test_images = [
        (
            "https://storage.googleapis.com/sfr-vision-language-research/BLIP/demo.jpg",
            "demo.jpg",
        ),
        # ("https://picsum.photos/400/300?random=1", "random1.jpg"),
        # ("https://picsum.photos/400/300?random=2", "random2.jpg"),
    ]

    print("\n📥 Загрузка тестовых изображений...")
    for url, filename in test_images:
        await client.download_test_image(url, filename)

    await client.test_single_prediction("test_images/demo.jpg")

    batch_images = [
        "test_images/demo.jpg",
        # "test_images/random1.jpg",
        # "test_images/random2.jpg",
    ]
    await client.test_batch_prediction(batch_images)

    print("\n✅ Тестирование завершено!")


if __name__ == "__main__":
    asyncio.run(main())
