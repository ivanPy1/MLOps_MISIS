import asyncio
import httpx
import time
import statistics
import requests
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
import os
import io
from PIL import Image

from .config import MONITORING_CONFIG
from .logger import (LOGGER, METRICS_LOGGER, COLORS, 
                    #  flush_metrics_logger
                     )

# --- Утилиты ---

def download_image(url: str, save_path: Path):
    """Скачивает изображение для тестирования."""
    if save_path.exists():
        return
    
    LOGGER.info(f"Загрузка тестового изображения: {url}")
    try:
        response = requests.get(url, timeout=MONITORING_CONFIG.monitoring["request_timeout_seconds"])
        response.raise_for_status()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(response.content)
        LOGGER.info(f"Изображение сохранено в: {save_path}")
    except requests.exceptions.RequestException as e:
        LOGGER.error(f"Ошибка загрузки изображения с {url}: {e}")
        raise

def get_test_image_data(image_path: Path) -> Dict[str, Any]:
    """Возвращает данные изображения для POST запроса."""
    try:
        if not image_path.exists():
            raise FileNotFoundError(f"Тестовое изображение не найдено: {image_path}")

        # Проверка, что это действительно изображение
        image = Image.open(image_path)
        img_byte_arr = io.BytesIO()
        # Сохраняем как JPEG для унификации, если нужно, иначе можно использовать image.format
        image.save(img_byte_arr, format='JPEG') 
        img_byte_arr.seek(0)
        
        return {
            "file": (image_path.name, img_byte_arr.read(), "image/jpeg")
        }
    except Exception as e:
        LOGGER.error(f"Ошибка чтения/обработки тестового изображения {image_path}: {e}")
        raise

# --- Логика мониторинга ---

class Monitor:
    """Основной класс мониторинга FastAPI сервиса."""

    def __init__(self):
        self.config = MONITORING_CONFIG
        self.base_url = self.config.service["base_url"]
        self.predict_url = self.base_url + self.config.monitoring["predict_endpoint"]
        self.health_url = self.base_url + self.config.monitoring["health_endpoint"]
        self.timeout = self.config.monitoring["request_timeout_seconds"]
        self.check_interval = self.config.monitoring["check_interval_seconds"]
        self.samples_per_check = self.config.monitoring["samples_per_check"]
        self.thresholds = self.config.thresholds
        self.alerts_enabled = self.config.alerts["enabled"]
        self.cooldown_minutes = self.config.alerts["cooldown_minutes"]
        self.last_alert_time = datetime.min
        self.consecutive_failures = 0
        
        # Скачиваем тестовое изображение при инициализации
        self.test_image_path = Path("test_images/monitor_test.jpg")
        try:
            download_image(self.config.monitoring["test_image_url"], self.test_image_path)
        except:
            LOGGER.critical("Не удалось загрузить тестовое изображение. Мониторинг инференса будет недоступен.")
            self.test_image_path = None
    
    
    async def run_single_prediction_test(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Выполняет один тест инференса и возвращает результат."""
        if not self.test_image_path:
            return {"success": False, "time_ms": self.timeout * 1000, "error": "Тестовое изображение недоступно"}
        
        start_time = time.time()
        
        try:
            files = get_test_image_data(self.test_image_path)
            response = await client.post(self.predict_url, files=files, timeout=self.timeout)
            
            end_time = time.time()
            time_ms = (end_time - start_time) * 1000
            
            success = response.status_code == 200
            
            if success:
                result_data = response.json().get("result", {})
                prediction = result_data.get("prediction", "N/A")
                success = result_data.get("success", False) # Проверка success из результата инференса
                
                LOGGER.info(f"✅ Prediction Test: Status 200, Time: {time_ms:.2f} ms, Prediction: {prediction[:30]}...")
                return {"success": success, "time_ms": time_ms, "prediction": prediction}
            else:
                LOGGER.warning(f"❌ Prediction Test: Status {response.status_code}, Time: {time_ms:.2f} ms, Error: {response.text[:50]}")
                return {"success": False, "time_ms": time_ms, "error": f"HTTP {response.status_code}: {response.text[:50]}"}
        
        except httpx.TimeoutException:
            LOGGER.error(f"⏰ Prediction Test: Timeout ({self.timeout}s)")
            return {"success": False, "time_ms": self.timeout * 1000, "error": "Timeout"}
        except Exception as e:
            LOGGER.error(f"❌ Prediction Test: Exception: {e}")
            return {"success": False, "time_ms": self.timeout * 1000, "error": str(e)}

    
    async def run_health_check(self, client: httpx.AsyncClient) -> bool:
        """Проверяет Health Status сервиса."""
        try:
            response = await client.get(self.health_url, timeout=self.timeout)
            is_healthy = response.status_code == 200
            if is_healthy:
                LOGGER.info(f"💚 Health Check OK: Status 200. Details: {response.json()}")
            else:
                LOGGER.critical(f"💔 Health Check FAILED: Status {response.status_code}. Response: {response.text}")
            return is_healthy
        except httpx.TimeoutException:
            LOGGER.critical(f"💔 Health Check FAILED: Timeout ({self.timeout}s)")
            return False
        except Exception as e:
            LOGGER.critical(f"💔 Health Check FAILED: Exception: {e}")
            return False

    
    def calculate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Вычисляет Response Time, P95 Latency и Error Rate."""
        times_ms = [r["time_ms"] for r in results]
        successful_requests = [r for r in results if r["success"]]
        successful_times = [r["time_ms"] for r in successful_requests]
        
        total_samples = len(results)
        success_count = len(successful_requests)
        error_count = total_samples - success_count
        
        # 1. Response Time (Average)
        response_time_ms = statistics.mean(times_ms) if times_ms else 0
        
        # 2. P95 Latency
        if times_ms:
            sorted_times = sorted(times_ms)
            p95_index = int(0.95 * total_samples) - 1
            if p95_index < 0: p95_index = 0
            p95_latency_ms = sorted_times[p95_index]
        else:
            p95_latency_ms = 0
        
        # 3. Error Rate
        error_rate_percent = (error_count / total_samples) * 100 if total_samples > 0 else 0

        # 4. Consecutive Failures (увеличиваем, если есть ошибки)
        if error_count > 0:
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "sample_size": total_samples,
            "response_time_ms": round(response_time_ms, 2),
            "p95_latency_ms": round(p95_latency_ms, 2),
            "error_rate_percent": round(error_rate_percent, 2),
            "consecutive_failures": self.consecutive_failures,
            "successful_requests": success_count,
            "failed_requests": error_count,
            "successful_times_ms": [round(t, 2) for t in successful_times],
        }
        
        METRICS_LOGGER.info("Monitoring Metrics", extra={"metrics": metrics})
        # flush_metrics_logger()
        
        return metrics

    
    def check_thresholds(self, metrics: Dict[str, Any]) -> str:
        """Проверяет метрики на соответствие порогам и возвращает статус."""
        status = "GREEN"
        alerts = []

        # Функция для проверки порога
        def check_metric(metric_name, value, threshold_type):
            nonlocal status
            thresholds = self.thresholds[metric_name]
            
            if value > thresholds["critical"]:
                alerts.append((f"{metric_name} CRITICAL: {value:.2f} > {thresholds['critical']}", "CRITICAL"))
                status = "RED"
            elif status != "RED" and value > thresholds["warning"]:
                alerts.append((f"{metric_name} WARNING: {value:.2f} > {thresholds['warning']}", "WARNING"))
                if status != "RED": status = "YELLOW"
        
        # 1. Response Time
        check_metric("response_time_ms", metrics["response_time_ms"], "Response Time")

        # 2. P95 Latency
        check_metric("p95_latency_ms", metrics["p95_latency_ms"], "P95 Latency")

        # 3. Error Rate
        check_metric("error_rate_percent", metrics["error_rate_percent"], "Error Rate")
        
        # 4. Consecutive Failures (специальная проверка)
        if metrics["consecutive_failures"] >= self.thresholds["consecutive_failures"]["critical"]:
            alerts.append((f"Consecutive Failures CRITICAL: {metrics['consecutive_failures']} >= {self.thresholds['consecutive_failures']['critical']}", "CRITICAL"))
            status = "RED"
        elif status != "RED" and metrics["consecutive_failures"] >= self.thresholds["consecutive_failures"]["warning"]:
            alerts.append((f"Consecutive Failures WARNING: {metrics['consecutive_failures']} >= {self.thresholds['consecutive_failures']['warning']}", "WARNING"))           
            if status != "RED": status = "YELLOW"

        self.handle_alerts(alerts, status)
        return status

    
    def handle_alerts(self, alerts: List[tuple], overall_status: str):
        """Логирование и управление системой алертов."""
        current_time = datetime.now()
        is_cooldown_active = (current_time - self.last_alert_time).total_seconds() < (self.cooldown_minutes * 60)

        # Вывод результатов
        if overall_status == "GREEN":
            LOGGER.info(f"{COLORS['GREEN']}🟢 SYSTEM STATUS: NORMAL{COLORS['ENDC']}")
        elif overall_status == "YELLOW":
            LOGGER.warning(f"{COLORS['YELLOW']}🟡 SYSTEM STATUS: WARNING{COLORS['ENDC']}")
        elif overall_status == "RED":
            LOGGER.critical(f"{COLORS['RED']}🔴 SYSTEM STATUS: CRITICAL{COLORS['ENDC']}")

        # Генерация алертов
        if not alerts or not self.alerts_enabled:
            return

        for message, level in alerts:
            if level == "CRITICAL":
                color = COLORS["RED"]
                logger_func = LOGGER.critical
            elif level == "WARNING":
                color = COLORS["YELLOW"]
                logger_func = LOGGER.warning
            else:
                continue

            alert_message = f"🚨 ALERT ({level}): {message}"
            
            if is_cooldown_active:
                LOGGER.info(f"Alert Suppressed (Cooldown): {message}")
            else:
                logger_func(f"{color}{alert_message}{COLORS['ENDC']}")
                self.last_alert_time = current_time # Сброс времени последнего алерта

    
    async def start_monitoring(self):
        """Основной цикл мониторинга."""
        LOGGER.info(f"🛠️  Запуск мониторинга сервиса {self.base_url}")
        LOGGER.info(f"   Интервал проверки: {self.check_interval}с, Запросов за раз: {self.samples_per_check}")
        
        async with httpx.AsyncClient() as client:
            while True:
                LOGGER.info("-" * 50)
                LOGGER.info(f"Начало цикла мониторинга: {datetime.now().strftime('%H:%M:%S')}")
                
                # 1. Health Check
                is_healthy = await self.run_health_check(client)
                
                if not is_healthy:
                    self.consecutive_failures += 1
                    status = self.check_thresholds({
                        "response_time_ms": self.timeout * 1000, 
                        "p95_latency_ms": self.timeout * 1000, 
                        "error_rate_percent": 100.0,
                        "consecutive_failures": self.consecutive_failures
                    })
                    LOGGER.critical(f"Сервис неработоспособен. Статус: {status}. Повторная попытка через {self.check_interval}с.")
                    await asyncio.sleep(self.check_interval)
                    continue
                
                # 2. Prediction Test Samples
                tasks = [self.run_single_prediction_test(client) for _ in range(self.samples_per_check)]
                results = await asyncio.gather(*tasks)
                
                # 3. Calculate and Log Metrics
                metrics = self.calculate_metrics(results)
                
                # 4. Check Thresholds and Handle Alerts
                self.check_thresholds(metrics)

                # 5. Wait for next check
                await asyncio.sleep(self.check_interval)


async def main_monitor():
    """Точка входа для запуска мониторинга."""
    if not MONITORING_CONFIG:
        LOGGER.critical("Не удалось загрузить конфигурацию. Мониторинг не запущен.")
        return

    monitor = Monitor()
    await monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main_monitor())