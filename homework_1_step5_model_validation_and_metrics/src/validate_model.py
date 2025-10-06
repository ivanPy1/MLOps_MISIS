import pickle
import pandas as pd
import yaml
import json
import sys
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


def load_params():
    """Загружает параметры из params.yaml"""
    with open("params.yaml", "r") as f:
        return yaml.safe_load(f)


def load_metrics():
    """Загружает метрики из metrics.json, если файл существует"""
    metrics_file = Path("metrics/metrics.json")
    if metrics_file.exists():
        with open(metrics_file, "r") as f:
            return json.load(f)
    return None


def calculate_accuracy(params):
    """Вычисляет accuracy модели на данных"""
    with open("models/model.pkl", "rb") as f:
        model = pickle.load(f)

    df = pd.read_csv("data/processed/dataset.csv")
    X = df[["total_bill", "size"]]
    y = df["high_tip"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=params["test_size"], random_state=params["seed"]
    )

    y_pred = model.predict(X_test)
    return accuracy_score(y_test, y_pred)


def validate_model():
    """Основная функция валидации модели"""
    try:
        # Загружаем параметры
        params = load_params()
        
        # Проверяем наличие минимального порога accuracy
        if "accuracy_min" not in params:
            print("Ошибка: параметр 'accuracy_min' не найден в params.yaml")
            sys.exit(1)
        
        accuracy_min = params["accuracy_min"]
        print(f"Минимальный порог accuracy: {accuracy_min:.4f}")

        # Пытаемся загрузить метрики из файла
        metrics = load_metrics()
        
        if metrics and "accuracy" in metrics:
            accuracy = metrics["accuracy"]
            print(f"Accuracy из metrics.json: {accuracy:.4f}")
            print("Используется accuracy из файла метрик")
        else:
            # Пересчитываем accuracy
            accuracy = calculate_accuracy(params)
            print(f"Пересчитанный accuracy: {accuracy:.4f}")
            print("Accuracy пересчитан на текущих данных")

        # Сравниваем с порогом
        print(f"Сравнение: {accuracy:.4f} >= {accuracy_min:.4f}")

        if accuracy >= accuracy_min:
            print("Валидация пройдена! Модель соответствует требованиям")
            sys.exit(0)
        else:
            print(f"Валидация провалена! Accuracy ниже минимального порога")
            print(f"Требуется: {accuracy_min:.4f}, получено: {accuracy:.4f}")
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"Ошибка: файл не найден - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    validate_model()
    