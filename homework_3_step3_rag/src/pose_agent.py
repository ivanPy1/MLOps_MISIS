import json
import textwrap
from typing import Any, Dict, List
from openai import OpenAI
import re

class PoseAgent:
    """
    Агент, использующий LLM для генерации логики (текстовых шагов танца).
    """
    def __init__(
        self,
        llm_base_url: str = "http://localhost:11434/v1",
        pose_api_url: str = "http://localhost:8001",
        model: str = "qwen2.5:1.5b",
    ):
        self.client = OpenAI(base_url=llm_base_url, api_key="ollama")
        self.pose_api_url = pose_api_url
        self.model = model

        # Инструмент для LLM: Генерация текстовых шагов
        self.step_tool = [
           
            {
                "type": "function",
                "function": {
                    "name": "list_dance_steps",
                    "description": "Сгенерировать список ключевых текстовых шагов или поз для выполнения танца.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "steps": {
                                "type": "array",
                                "description": "Список из 12 коротких текстовых описаний ключевых шагов танца, например: 'правая рука на левое плечо', 'руки вперед ладонями вниз'.",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["steps"],
                    },
                }
            }
        ]

    def chat(self, user_prompt: str) -> Dict:
        """
        Основной метод. Вызывает LLM для генерации списка текстовых шагов.
        Возвращает список шагов или ошибку.
        """
        
        system_message = textwrap.dedent(f"""\
            Твоя задача — проанализировать запрос пользователя (например, название танца) и сгенерировать 
            последовательность ключевых текстовых шагов, используя функцию `list_dance_steps`. 
            Не генерируй координаты и не предлагай никаких других действий. Количество шагов не менее 12.

            
        """)
        
        steps_messages = [{"role": "system", "content": system_message}]
        steps_messages.append({"role": "user", "content": user_prompt})

        try:
            steps_response = self.client.chat.completions.create(
                model=self.model,
                messages=steps_messages,
                tools=self.step_tool,
                tool_choice={"type": "function", "function": {"name": "list_dance_steps"}},
            )
        except Exception as e:
            return {"error": f"Error during Step 1 chat completion: {e}", "success": False}

        steps_message = steps_response.choices[0].message
        
        # 1. Сценарий успеха: LLM использовал Function Call
        if steps_message.tool_calls:
            
            tool_call = steps_message.tool_calls[0]
            if tool_call.function.name == "list_dance_steps":
                try:
                    steps_args = json.loads(tool_call.function.arguments)
                    generated_steps = steps_args.get("steps", [])
                    
                    if not generated_steps:
                        return {"error": "LLM generated an empty list of steps.", "success": False}
                        
                   
                    return {"steps": generated_steps, "success": True}
                    
                except json.JSONDecodeError:
                    return {"error": "LLM returned invalid JSON for dance steps.", "success": False}
        
        # 2. Сценарий отката: LLM не вызвал инструмент, но выдал текстовый ответ
        raw_content = steps_message.content
        if raw_content:
            print("  [LLM] Внимание: LLM не использовал инструмент, но выдал шаги в тексте. Парсинг текста...")
            
            # 1. Удаляем все не-кириллические символы (например, '右手') и лишние пробелы.
            clean_content = re.sub(r'[^\w\s,а-яА-Я]', '', raw_content)
            
            # 2. Разбиваем по запятым и очищаем
            steps_from_text = [step.strip() for step in clean_content.split(',') if step.strip() and len(step.strip().split()) > 1]
            
            if steps_from_text:
                return {"steps": steps_from_text, "success": True}
            
            # Если текст был, но не удалось его распарсить как список
            return {"text": raw_content, "success": False}
            
        # 3. Полный сбой
        return {"text": "LLM failed to call list_dance_steps and returned no content.", "success": False}

    def reset_conversation(self):
        pass