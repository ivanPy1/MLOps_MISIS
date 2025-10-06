"""
Тест Pose Agent (функциональный).

Проверяет, что PoseAgent корректно вызывает LLM и получает от него 
структурированный ответ с непустым списком текстовых шагов ('steps').
"""

import sys
import time
from typing import List

# Добавляем текущую директорию в PYTHONPATH для корректного импорта
sys.path.insert(0, ".")

try:
    # Импорт PoseAgent
    from src.pose_agent import PoseAgent
except ImportError as e:
    print(f"❌ Критическая ошибка импорта: Не удалось импортировать PoseAgent. Ошибка: {e}")
    sys.exit(1)


def test_agent_function_calling():
    """
    Проверяет, что chat() вызывает LLM и возвращает структурированный 
    ответ с непустым списком шагов для танца.
    """
    print("🤖 Функциональный тест Pose Agent (Генерация шагов)")
    print("=" * 60)

    try:
        # Agent инициализируется без RAG/API, как чистый LLM-агент.
        agent = PoseAgent()
        print("✅ Agent инициализирован.")
    except Exception as e:
        print(f"❌ Ошибка инициализации Agent: {e}")
        # Возвращаем False, чтобы тест был провален
        return False

    # Кейсы, которые должны вызвать генерацию списка шагов
    test_cases = [
        "Сгенерируй шаги для танца макарена",
        "танец макарена"
    ]

    all_passed = True
    for i, message in enumerate(test_cases, 1):
        print(f"\n{i}. Тест с запросом: '{message}'")
        start_time = time.time()
        
        try:
            # Ожидаем: {'steps': List[str], 'success': True}
            result = agent.chat(message)
            
            # 1. Проверка успеха
            if not result.get('success'):
                print("❌ Тест провален: 'success' == False.")
                print(f"   Ошибка LLM: {result.get('error', result.get('text', 'Неизвестная ошибка.'))}")
                all_passed = False
                continue

            # 2. Проверка наличия и типа 'steps'
            steps: List[str] = result.get('steps')
            
            if 'steps' not in result:
                raise AssertionError("Ответ LLM не содержит обязательный ключ 'steps'.")
            
            if not isinstance(steps, list):
                raise AssertionError("Значение 'steps' не является списком.")
                
            if not len(steps) > 0:
                raise AssertionError("Список шагов пуст.")
            
            end_time = time.time()
            print(f"✅ Тест пройден: Получен список из {len(steps)} шагов за {end_time - start_time:.2f}с.")
            
        except AssertionError as e:
            print(f"❌ Тест провален (Ошибка структуры данных): {e}")
            all_passed = False
        except Exception as e:
            print(f"❌ Общая ошибка при выполнении chat(): {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
            
    print("\n--------------------------------------------------")
    if all_passed:
        print("🎉 Функциональный тест PoseAgent пройден успешно.")
    else:
        print("🛑 Функциональный тест PoseAgent провален.")
        
    return all_passed


if __name__ == "__main__":
    success = test_agent_function_calling()
    # Возвращаем код 0 в случае успеха, 1 в случае провала
    sys.exit(0 if success else 1)