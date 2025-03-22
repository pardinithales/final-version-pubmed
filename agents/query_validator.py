from anthropic import Anthropic, APIError
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class QueryValidator:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY não definida no .env")
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-7-sonnet-20250219"

    def validate_query(self, user_query):
        if len(user_query) < 10 or not any(c.isalpha() for c in user_query):
            logger.error("Query inválida: muito curta ou sem letras.")
            return False, None
        
        prompt = f"""
        Analise a seguinte query: "{user_query}"
        Verifique se ela contém pelo menos:
        1. Uma população específica (ex.: "pacientes com diabetes", "high-grade glioma")
        2. Uma intervenção (ex.: "tratamento com insulina", "ENT")
        Responda no formato:
        "Sim\nTradução: <query em inglês com termos genéricos>"
        ou "Não" se inválida.
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.8,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            response = message.content[0].text.strip()
            logger.debug(f"Resposta da LLM para validação: {response}")
            if "Sim" in response:
                translated_query = response.split("\nTradução: ")[1].strip()
                return True, translated_query
            return False, None
        except APIError as e:
            logger.error(f"Erro na API Anthropic: {e}")
            return False, None
        except IndexError:
            logger.error("Erro ao parsear tradução da LLM.")
            return False, None