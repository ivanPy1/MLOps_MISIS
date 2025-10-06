# 🕺 RAG-система для генерации анимаций из текстовых описаний

## Описание проекта

Данный проект реализует **RAG-систему (Retrieval-Augmented Generation)** для преобразования высокоуровневых текстовых запросов (например, названия танца) в последовательность двумерных поз, которые затем визуализируются в виде GIF-анимации.

Система использует **Large Language Model (LLM)** для интерпретации запроса и модули на Python для поиска, ранжирования и финальной сборки данных, что обеспечивает **корректность координат** и **высокое качество** выходной анимации.

### Цель проекта

Главная цель — создать GIF-анимацию танца **"Макарена"** по текстовому запросу `"танец макарена"`.

---

## 🏗️ Архитектура и компоненты RAG

Процесс генерации анимации делится на три ключевых этапа (LLM-Logic, Retriever/Reranker, Generator):

### 1. LLM-Logic (Генерация шагов)
* **Инструмент:** **PoseAgent** (файл `pose_agent.py`).
* **Задача:** Получить текстовый запрос и, используя **Function Calling**, сгенерировать последовательность **текстовых шагов** или поз (например, `"правая рука на левое плечо"`).
* **Сервис:** **Ollama** (модель qwen2.5:1.5b) на порту `11434`.

### 2. Retriever & Reranker (Поиск и ранжирование поз)
* **Инструмент:** Python-логика в файле `demo_macarena_direct.py`.
* **Задача:** Преобразовать текстовые шаги, сгенерированные LLM, в точные координаты поз.
    * **База данных:** `poses_database.json`
    * **Retriever:** Использует поиск по ключевым словам (части тела, направления) для нахождения потенциально релевантных поз по их описаниям.
    * **Reranker:** Применяет **MMR-подобную** логику для выбора наиболее релевантных *и* разнообразных поз, формируя финальную последовательность.
* **Результат:** Список JSON-объектов поз с проверенными координатами.

### 3. Generator (Визуализация)
* **Инструмент:** **Pose API** (файл `pose_api.py`).
* **Задача:** Принять финальный список поз и визуализировать каждый кадр, а затем собрать их в итоговый GIF-файл.
* **Сервис:** FastAPI-сервис на порту `8001`.

---

## 💾 База данных поз (`poses_database.json`)

База данных содержит записи с проверенными координатами и русскоязычное описание.

**Пример структуры позы:**
```json
{
  "pose": {
    "Torso": [0, 0],
    "Head": [0, 60],
    "RH": [30, 35],
    "LH": [-30, 35],
    "RK": [15, -50],
    "LK": [-15, -50]
  },
  "description": "Руки вытянуты вперед на уровне плеч, ноги на ширине плеч"
}
```
## Структура

```
step3_homework_2_rag/
├── src/
│   ├── __init__.py
│   ├── pose_api.py           # API визуализации поз
│   └── pose_agent.py         # LLM агент с function calling
│── test_scripts/
│   ├── demo_animation.py # Демонстрация создания анимации без LLM
│   ├── demo_macarena_direct.py # Генерация gif "танец макарена"
│   └── demo_simple.py         # Простая демонстрация без LLM - прямое использование API
│   └── test_agent.py         # Тест Pose Agent (функциональный).
│   └── test_debug_agent.py   # Тест отладки (Debug Test) для PoseAgent.
│   └── test_imports.py         # Проверка импортов
│   └── test_oolama_connection.py # Quick Ollama connection test 
│   └── test_pose_api.py # Тест Pose API без vLLM
├── docker-compose.yml        # vLLM + Pose API
├── Dockerfile.pose           # Docker для Pose API
├── test_imports.py          # Проверка импортов
├── pyproject.toml           # Poetry зависимости
├── Makefile                 # Команды автоматизации
├── poses_database.json # База данных с позами
└── README.md
```
## Установка

```bash
# Установка зависимостей
make install

# Или вручную
poetry install
```

## Запуск

### 1. Запуск всех сервисов

```bash
# Запуск vLLM и Pose API
make start-all
```


Это запустит:
- vLLM сервер на `http://localhost:8000`
- Pose Visualization API на `http://localhost:8001`

**Важно**: Первый запуск займёт несколько минут для загрузки модели.

```bash
# Pulling qwen2.5:1.5b model
make pull
```
### 2. Проверка логов

```bash
# Логи ollama_server
make logs-ollama

# Логи Pose API
make logs-pose
```

### 3. Создаем и активируем виртуальное окружение
``` bash
# Создание вирутального окружения
python -m venv .venv

# Активация для Windows
.venv\Scripts\activate

# Активация для Linux/macOS
source .venv/bin/activate
```

### 4. Запуск RAG-системы для генерации GIF анимации по запросу "танец макарена" 
``` bash
make generate-macarena-gif

# Результат в demo_animations/macarena_mmr_rag_animation.gif
```
### 5. Тесты 
``` bash
make test-agent              # Тест генерации шагов для танца макарена
make test-debug-agent        # Тест отладки (Debug Test) для PoseAgent
make test-imports            # Проверка импортов и компонентов PoseAgent
make test-ollama-connection  # Quick Ollama connection test
make test-api                # Тест Pose API без vLLM
```