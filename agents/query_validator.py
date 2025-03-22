# C:\Users\Usuario\Desktop\projetos\PUBMED_CREW\agents\query_validator.py
from anthropic import Anthropic, APIError
import logging
import os
from dotenv import load_dotenv
from typing import Tuple

load_dotenv()

logger = logging.getLogger(__name__)

class QueryValidationError(Exception):
    pass

class QueryValidator:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY não definida no .env")
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-7-sonnet-20250219"

    def validate_query(self, user_query: str) -> Tuple[bool, str | None]:
        """
        Valida a query usando a API Anthropic e retorna se é válida e a tradução em inglês.
        Retorna (is_valid, translated_query).
        """
        if len(user_query) < 10 or not any(c.isalpha() for c in user_query):
            logger.error("Query inválida: muito curta ou sem letras.")
            return False, None
        
        prompt = f"""
        Analise a seguinte query: "{user_query}"
        Verifique se ela contém pelo menos um dos seguintes:
        1. Uma população específica (ex.: "pacientes com diabetes", "high-grade glioma")
        2. Uma intervenção (ex.: "tratamento com insulina", "ENT", "TTFields")
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

def validate_and_raise(query: str) -> str:
    """
    Valida a query e levanta exceção se inválida, retornando a tradução se válida.
    """
    validator = QueryValidator()
    is_valid, translated_query = validator.validate_query(query)
    if not is_valid:
        raise QueryValidationError("Query inválida: deve conter uma população específica ou uma intervenção.")
    return translated_query