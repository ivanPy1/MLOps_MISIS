import pickle
import pandas as pd
import yaml
import json
import uuid
from datetime import datetime
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


def load_params():
    with open("params.yaml", "r") as f:
        return yaml.safe_load(f)


def evaluate_model():
    params = load_params()

    with open("models/model.pkl", "rb") as f:
        model = pickle.load(f)

    df = pd.read_csv("data/processed/dataset.csv")

    X = df[["total_bill", "size"]]
    y = df["high_tip"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=params["test_size"], random_state=params["seed"]
    )

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    # Создаем директорию для метрик, если она не существует
    Path("metrics").mkdir(exist_ok=True)
    
    # Генерируем уникальный ID и временную метку
    evaluation_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    # Формируем данные для сохранения
    metrics_data = {
        "evaluation_id": evaluation_id,
        "timestamp": timestamp,
        "accuracy": round(accuracy, 4),
        "dataset_size": len(df),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "model_parameters": {
            "test_size": params["test_size"],
            "random_state": params["seed"]
        }
    }
    
    # Сохраняем метрики в JSON файл
    with open("metrics/metrics.json", "w") as f:
        json.dump(metrics_data, f, indent=4)
    
    print(f"Evaluation ID: {evaluation_id}")
    print(f"Timestamp: {timestamp}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Dataset size: {len(df)} rows")
    print(f"Train size: {len(X_train)} rows") 
    print(f"Test size: {len(X_test)} rows")
    print("Metrics saved to metrics/metrics.json")


if __name__ == "__main__":
    evaluate_model()
    