"""
Проверка импортов и компонентов PoseAgent после рефакторинга.
PoseAgent теперь отвечает только за логику LLM (генерацию текстовых шагов) 
и не содержит RAG-компонентов (Retriever).
"""

import sys
import os
import json

# Добавляем текущую директорию в PYTHONPATH для возможности импорта pose_agent
sys.path.insert(0, ".")

# --- Попытка импорта PoseAgent ---
try:
    # Пытаемся импортировать из текущей директории
    from src.pose_agent import PoseAgent
except ImportError as e:
    print(f"❌ Критическая ошибка импорта: Не удалось импортировать PoseAgent из pose_agent.py. Ошибка: {e}")
    sys.exit(1)


def test_imports_and_agent_structure():
    """
    Проверяет, что PoseAgent импортируется корректно 
    и соответствует новой структуре (LLM-Logic Only).
    """
    print("🤖 Запуск проверки структуры PoseAgent")
    print("=" * 60)
    
    try:
        # 1. Инициализация Агента
        agent = PoseAgent()
        print("✅ PoseAgent успешно импортирован и инициализирован")
        
        # 2. Проверка основных методов
        assert hasattr(PoseAgent, "chat")
        assert hasattr(PoseAgent, "reset_conversation")
        print("✅ PoseAgent методы (chat, reset_conversation) OK")
        
        # 3. Проверка инструмента (должен быть только один: list_dance_steps)
        assert hasattr(agent, "step_tool")
        assert isinstance(agent.step_tool, list)
        assert len(agent.step_tool) == 1
        
        # Проверяем, что единственный инструмент — это list_dance_steps
        tool = agent.step_tool[0]
        assert tool['type'] == 'function'
        assert tool['function']['name'] == 'list_dance_steps'
        print("✅ Agent имеет 1 инструмент: 'list_dance_steps'")

        # 4. Проверка разделения обязанностей (RAG-контроль)
        # В соответствии с новой архитектурой, Agent не должен содержать базу данных.
        assert not hasattr(agent, "pose_database")
        print("✅ RAG-контроль: Атрибут 'pose_database' отсутствует. Agent чист и готов к работе с внешним Retriever.")
        
        print("--------------------------------------------------")
        print("🎉 Тест импортов и структуры PoseAgent пройден успешно!")
        return True
    
    except AssertionError as e:
        print(f"❌ Ошибка утверждения: Один из компонентов PoseAgent отсутствует или некорректен.")
        # Выводим детали, если они есть
        if str(e):
             print(f"   Детали: {e}")
        return False
    
    except Exception as e:
        print(f"❌ Общая ошибка в тесте: {e}")
        return False


if __name__ == "__main__":
    success = test_imports_and_agent_structure()
    # Возвращаем код 0 в случае успеха, 1 в случае ошибки
    sys.exit(0 if success else 1)