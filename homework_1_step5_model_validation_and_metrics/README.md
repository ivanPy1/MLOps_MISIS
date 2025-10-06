# Homework Step 5: model validation and metrics

Полнофункциональный pipeline машинного обучения с валидацией данных и мониторингом качества модели.

### Добавлено:
1. Интегрирован poetry для управления зависимостями и настроен pre-commit хуки для автоматического форматирования и проверки кода. Это обеспечивает стандарты кодирования и консистентность проекта.
Включены в .pre-commit-config.yaml следующие хуки: black, ruff, isort, end-of-file-fixer, 
check-yaml.

2. Модифицирован скрипт scr/evaluate.py, так что он записывает метрики accuracy, dataset_size, train_sizeб test_size в файл metrics/metrics.json

3. Реализован src/validate_model.py, который выполняет проверку качества модели. 
Скрипт:
    - читает модель и данные
    - читает метрику accuracy из metrics/metrics.json
    - сравнивает полученную accuracy с порогом accuracy_min, заданным в params.yaml
    - в случае нарушения порого (accuracy  < accuracy_min) завершается с кодов выхода, отличным от 0, чтобы
    сигнализировать о проавле валидации


4. обновлен dvc.yaml:
    - в стадии evaluate указан файл metrics/metrics.json как отслеживаемые метрики (metrics: metrics/metrics.json)
    - добавлена новая стадия validate_model, которая будет запускаться после evaluate
    - определены зависимости для стадии validate_model: validate_model.py, обученная модель (models/model.pkl) и params.yaml

---


## 🚀 Особенности

- **Автоматическая валидация данных** с проверкой на null и допустимые диапазоны значений
- **Валидация качества модели** по пороговым значениям accuracy
- **Поэтапный DVC pipeline** с воспроизводимыми результатами
- **Автоматическое форматирование кода** через pre-commit хуки
- **Подробные отчеты** в HTML формате

## 📦 Быстрый старт

### Установка зависимостей

```bash
# Установка Poetry (если не установлен)
curl -sSL https://install.python-poetry.org | python3 -

# Клонирование и установка
git clone https://github.com/ivanPy1/MLOps_MISIS
cd step5_homework_model_validation_and_metrics
poetry install

```

## 🚀 Запуск полного pipeline

### Установка и настройка
```bash
make install 
make pre-commit       
dvc init
dvc remote add -d local ../../.dvcstore
```

### Запуск
```bash
dvc repro
```

## 📊 Pipeline этапы

1. Загрузка данных (get_data)
```bash
python src/get_data.py
```

* Загружает данные из внешнего источника
* Сохраняет в data/raw/tips.csv

2. Валидация данных(validate_data)
```bash
python src/validate_data.py
```

Проверяет:
* Отсутствие null значений в total_bill, tip, size
* total_bill в диапазоне [0, 100]
* size в диапазоне [1, 10]

3. Предобработка (preprocess)
```bash
python src/preprocess.py
```

* Создает признак high_tip (чаевые > 20% от счета)
* Сохраняет обработанные данные в data/processed/dataset.csv

 4. Обучение модели (train)
```bash
python src/train.py
```

* Обучает Logistic Regression модель
* Сохраняет модель в models/model.pkl

5. Оценка модели (evaluate)
```bash
python src/evaluate.py
```

* Вычисляет метрики качества
* Сохраняет в metrics/metrics.json

6. Валидация модели (validate_model)
```bash
python src/validate_model.py
```

## Конфигурация

### Параметры (params.yaml)
```bash
seed: 42
test_size: 0.2
accuracy_min: 0.9  # Минимальный порог accuracy
urls:
  tips: https://raw.githubusercontent.com/mwaskom/seaborn-data/master/tips.csv
```
## Pre-commit хуки (.pre-commit-config.yaml)

* ✅ black - форматирование кода

* ✅ ruff - линтинг

* ✅ isort - сортировка импортов

* ✅ end-of-file-fixer - исправление файлов

* ✅ check-yaml - валидация YAML

## 📁 Структура проекта
```text
.
├── src/
│   ├── get_data.py         # Загрузка данных
│   ├── validate_data.py    # Валидация (Great Expectations)
│   ├── preprocess.py       # Предобработка
│   ├── train.py           # Обучение модели
│   ├── evaluate.py        # Оценка метрик
│   └── validate_model.py  # Валидация модели
├── data/
│   ├── raw/               # Исходные данные
│   └── processed/         # Обработанные данные
├── models/                # Обученные модели
├── metrics/               # JSON метрики
├── reports/               # HTML отчеты
├── params.yaml           # Параметры
├── dvc.yaml              # DVC pipeline
└── Makefile              # Автоматизация
```