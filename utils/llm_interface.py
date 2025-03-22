from openai import OpenAI, OpenAIError
import os
import logging

logger = logging.getLogger(__name__)

class LLMInterface:
    def __init__(self):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY não definida no .env")
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self.model = "deepseek-reasoner"

    def generate(self, prompt):
        logger.debug(f"Enviando prompt para DeepSeek: {prompt}")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=int(os.getenv("DEFAULT_MAX_OUTPUT_TOKENS", 4000)),
                stream=False
            )
            content = response.choices[0].message.content
            logger.debug(f"Resposta da DeepSeek: {content}")
            return content
        except OpenAIError as e:
            logger.error(f"Erro na API DeepSeek: {e}")
            return "Erro na resposta da LLM"
        except Exception as e:
            logger.error(f"Erro inesperado ao chamar DeepSeek API: {e}")
            return "Erro desconhecido"