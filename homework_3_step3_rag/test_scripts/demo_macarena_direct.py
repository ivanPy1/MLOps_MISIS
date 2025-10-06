"""
Скрипт для демонстрации СБОРКИ JSON В PYTHON с использованием 
RAG (Retriever-Reranker-Generator).
1. LLM генерирует текстовые шаги (через PoseAgent).
2. Python (Retriever) извлекает потенциальные позы из базы данных.
3. Python (Reranker) применяет логику, имитирующую MMR для выбора 
   наиболее релевантных и разнообразных поз.
4. Python собирает финальный JSON (список поз).
5. Python валидирует и создает GIF.
"""

import base64
import io
import json
import math
import os
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests
from PIL import Image

sys.path.insert(0, ".")

try:
    from src.pose_agent import PoseAgent
except ImportError:
    try:
        from src.pose_agent import PoseAgent 
    except ImportError:
        print("❌ Критическая ошибка импорта: Не удалось импортировать PoseAgent.")
        exit(1)


# --- Конфигурация ---
POSE_DATABASE_PATH = "poses_database.json"
OUTPUT_DIR = Path("demo_animations")
OUTPUT_FILENAME = "macarena_mmr_rag_animation.gif"
POSE_API_URL = "http://localhost:8001"
QUERY = "танец макарена"

# Используются только слова, связанные с частями тела и движением, которые должны быть в описаниях базы данных.
POSE_KEYWORDS = {
    'рука', 'руки', 'нога', 'ноги', 'плечо', 'колено', 'голова', 'тело', 'корпус', 
    'вверх', 'вниз', 'стороны', 'сторону', 'вперед', 'назад', 'прямые', 'согнуты', 
    'вместе', 'разведены', 'бок', 'слегка' 
}

def _load_pose_database(path: str) -> List[Dict]:
    """Загружает базу данных поз из JSON файла."""
    if not os.path.exists(path):
        print(f"Error: Pose database file not found at {path}. Aborting.")
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {path}. Aborting.")
        return []

def calculate_relevance_score(step_keywords: set, description: str) -> float:
    """
    Имитация метрики релевантности: отношение совпадений ключевых слов 
    к общему числу уникальных ключевых слов.
    """
    desc_words = set(description.lower().split())
    matched_words = step_keywords.intersection(desc_words)
    if not step_keywords:
        return 0.0
    return len(matched_words) / len(step_keywords)

def calculate_diversity_penalty(pose_index: int, selected_poses_indices: List[int]) -> float:
    """
    Имитация метрики разнообразия (штраф за близость в базе данных).
    """
    if not selected_poses_indices:
        return 0.0
    
    min_distance = min(abs(pose_index - selected_idx) for selected_idx in selected_poses_indices)
    penalty = 1.0 / (min_distance + 1)
    
    penalty += random.uniform(0.0, 0.2)
    
    return min(penalty, 1.0)

def retrieve_and_rerank_poses(steps: List[str], pose_database: List[Dict], count: int = 8, lambda_mmr: float = 0.5) -> List[Dict]:
    """
    Реализует Retriever и Reranker (MMR-подобная логика).
    """
    print("  [Retriever] Инициализация поиска потенциальных поз...")
    
    # 1. Сбор и фильтрация ключевых слов из сгенерированных шагов
    all_step_words = {word.lower() for step in steps for word in step.split()}
    step_keywords = all_step_words.intersection(POSE_KEYWORDS)
    
    if not step_keywords:
        # Если фильтр убрал все, используем более широкие слова (>2 символов) как запасной вариант
        step_keywords = {word.lower() for word in all_step_words if len(word) > 2}
        if not step_keywords:
            print("  [Retriever] Нет ключевых слов для поиска. Сброс.")
            return []
        print(f"  [Retriever] Предупреждение: используется широкий поиск с {len(step_keywords)} словами.")

    # 2. Инициализация и расчет релевантности (RAG-часть)
    candidate_poses: List[Tuple[int, Dict, float]] = []
    
    for i, entry in enumerate(pose_database):
        description = entry.get('description', '').lower()
        pose = entry.get('pose')

        if pose:
            # Расчет релевантности на основе очищенных ключевых слов
            relevance_score = calculate_relevance_score(step_keywords, description)
            if relevance_score > 0.0:
                candidate_poses.append((i, pose, relevance_score))

    if not candidate_poses:
        print("  [Retriever] Не найдено потенциальных релевантных поз.")
        return []
        
    # 3. Reranker: Выбор по MMR-подобной метрике
    print("  [Reranker] Запуск MMR логики для выбора поз...")
    final_poses_indices: List[int] = []
    final_poses: List[Dict] = []
    
    while len(final_poses) < count and candidate_poses:
        best_mmr_score = -math.inf
        best_candidate = None
        best_candidate_index_in_candidates = -1
        
        for idx_in_candidates, (pose_idx, pose, rel_score) in enumerate(candidate_poses):
            div_penalty = calculate_diversity_penalty(pose_idx, final_poses_indices)
            
            mmr_score = (lambda_mmr * rel_score) - ((1 - lambda_mmr) * div_penalty)
            
            if mmr_score > best_mmr_score:
                best_mmr_score = mmr_score
                best_candidate = (pose_idx, pose, rel_score)
                best_candidate_index_in_candidates = idx_in_candidates
        
        if best_candidate:
            pose_idx, pose, rel_score = best_candidate
            final_poses_indices.append(pose_idx)
            final_poses.append(pose)
            
            candidate_poses.pop(best_candidate_index_in_candidates)
        else:
            break

    return final_poses


def validate_pose_structure(poses: List[Dict[str, Any]]):
    """
    Строго проверяет, что список поз соответствует требуемой JSON-схеме.
    """
    if not isinstance(poses, list) or not poses:
        raise ValueError("Финальный список поз пуст или не является списком.")
    
    required_keys = {"Torso", "Head", "RH", "LH", "RK", "LK"}
    
    for i, pose in enumerate(poses):
        if set(pose.keys()) != required_keys:
            raise KeyError(f"Поза {i} имеет неверный набор ключей. Ожидаются: {required_keys}")
        
        for key in required_keys:
            coords = pose[key]
            if not (isinstance(coords, list) and len(coords) == 2 and all(isinstance(coord, (int, float)) for coord in coords)):
                raise TypeError(f"Координаты для {key} в позе {i} не являются списком из двух чисел [x, y].")

    print(f"✅ Валидация JSON: Найден список поз, соответствующий схеме.")


def generate_animation_gif_from_poses(poses_list: List[Dict], pose_api_url: str, gif_path: Path):
    """
    Создает GIF из списка поз, отправляя каждую позу в API.
    """
    frames = []
    print("\n⚙️ Запуск генерации GIF, отправка поз в API...")
    
    for i, pose in enumerate(poses_list):
        try:
            # Отправляем каждую позу в API: "http://localhost:8001/visualize"
            response = requests.post(
                f"{pose_api_url}/visualize",
                json={"pose": pose},
                timeout=5,
            )
            response.raise_for_status()
            result = response.json()

            if result.get("success") and result.get("image"):
                img_data = base64.b64decode(result["image"])
                img = Image.open(io.BytesIO(img_data))
                frames.append(img)
            else:
                print(f"  ✗ Кадр {i+1} не сгенерирован. Ответ API: {result}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Ошибка подключения к Pose API при генерации кадра: {e}")
            print("   Проверьте, запущен ли `pose_api.py` на порту 8001.")
            return False

    if frames:
        # Сборка и сохранение GIF
        frames[0].save(
            gif_path,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=400, 
            loop=0,
        )
        return True
    return False


def main():
    print(f"🎬 Запуск RAG-системы (LLM-Logic + Python-Data) для запроса: '{QUERY}'")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    gif_path = OUTPUT_DIR / OUTPUT_FILENAME

    try:
        # 1. Инициализация. Загрузка базы данных в главный скрипт.
        agent = PoseAgent()
        pose_database = _load_pose_database(POSE_DATABASE_PATH)
        
        if not pose_database:
             print("❌ База данных поз не загружена.")
             return

        start_time = time.time()

        # 2. Получение текстовых шагов от LLM
        llm_result = agent.chat(user_prompt=QUERY)

        if not llm_result.get("success") or "steps" not in llm_result:
            print("\n❌ LLM не сгенерировал список шагов:")
            print(f"   Причина: {llm_result.get('error', llm_result.get('text', 'Неизвестная ошибка.'))}")
            return

        generated_steps = llm_result["steps"]

        # 3. Python Retriever & Reranker: Сборка финального JSON
        poses_list = retrieve_and_rerank_poses(generated_steps, pose_database, count=8, lambda_mmr=0.6)
        
        if not poses_list:
            print("\n❌ Retriever/Reranker не нашел релевантных поз в базе данных.")
            return
            
        print(f"  [Reranker] Собрана финальная последовательность поз.")

        # 4. Валидация
        try:
            validate_pose_structure(poses_list)
        except (ValueError, TypeError, KeyError) as e:
            print(f"\n❌ Критическая ошибка: Неверная структура собранного JSON. Причина: {e}")
            return

        # 5. Генерация GIF
        success = generate_animation_gif_from_poses(poses_list, POSE_API_URL, gif_path)
        end_time = time.time()
        
        if success:
            print(f"\n🎉 Анимация успешно сгенерирована и сохранена!")
            print(f"   Файл: {gif_path.resolve()}")
            print(f"   🕒 Общее время: {end_time - start_time:.2f} с")
            
    except Exception as e:
        print(f"\nКритическая ошибка в скрипте: {e}")
        import traceback
        traceback.print_exc()
        print("Проверьте установленные зависимости и запуск сервисов (Ollama:11434, Pose API:8001).")

if __name__ == "__main__":
    main()
    