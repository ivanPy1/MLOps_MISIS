"""
Тест отладки (Debug Test) для PoseAgent.

Проверяет, что:
1. Agent корректно инициализируется.
2. Метод chat() успешно вызывает LLM с Function Calling.
3. chat() возвращает структурированный ответ с непустым списком текстовых шагов ('steps'), 
   соответствующий инструменту list_dance_steps.
"""

import sys
import json
from typing import List, Dict, Any

# Добавляем текущую директорию в PYTHONPATH для корректного импорта
sys.path.insert(0, ".")

# Улучшенная обработка импорта PoseAgent
try:
    from src.pose_agent import PoseAgent
except ImportError as e:
    print(f"❌ Критическая ошибка импорта: Не удалось импортировать PoseAgent. Проверьте pose_agent.py. Ошибка: {e}")
    sys.exit(1)


def test_agent_steps_generation():
    """Проверяет генерацию текстовых шагов LLM."""
    print("\n🤖 Тест Pose Agent (Генерация шагов)")
    print("=" * 60)

    # Agent инициализируется без путей к RAG/API, так как он чистый LLM-агент.
    try:
        agent = PoseAgent()
        print("✅ Agent инициализирован.")
    except Exception as e:
        print(f"❌ Ошибка инициализации Agent: {e}")
        return False

    test_prompt = "Сгенерируй шаги для танца макарена"

    print(f"\n1. LLM Тест с запросом: '{test_prompt}'")

    try:
        # LLM должен вернуть {'steps': List[str], 'success': True}
        result = agent.chat(test_prompt)
        
        # 1. Проверка успеха
        if not result.get('success'):
            print("❌ Тест провален: 'success' == False.")
            print(f"   Ошибка LLM: {result.get('error', result.get('text', 'Неизвестная ошибка.'))}")
            return False

        # 2. Проверка наличия и типа 'steps'
        steps: List[str] = result.get('steps')
        assert isinstance(steps, list), "Результат 'steps' не является списком."
        assert len(steps) > 0, "Список шагов пуст."
        assert all(isinstance(step, str) for step in steps), "Некоторые элементы в списке шагов не являются строками."
        
        # 3. Вывод результатов
        print(f"✅ Тест пройден: Получен структурированный ответ.")
        print(f"   Количество шагов: {len(steps)}")
        print("   Сгенерированные шаги:")
        for i, step in enumerate(steps):
            print(f"     {i+1}. {step}")
            
        return True

    except AssertionError as e:
        print(f"❌ Тест провален (Ошибка структуры данных): {e}")
        return False
        
    except Exception as e:
        print(f"❌ Общая ошибка при выполнении chat(): {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_agent_steps_generation()
    sys.exit(0 if success else 1)