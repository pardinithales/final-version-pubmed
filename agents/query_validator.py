import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class QueryValidator:
    def __init__(self):
        self.population_keywords = [
            "patients", "individuals", "people", "adults", "children",
            "glioma", "glioblastoma", "high-grade glioma", "brain tumor",
            "brain cancer", "malignant glioma", "cancer"
        ]
        self.intervention_keywords = [
            "treatment", "therapy", "treated with", "using", "ENT",
            "TTFields", "TTS field", "tumor treating fields", "Optune"
        ]

    def validate_query(self, user_query):
        if len(user_query) < 10 or not any(c.isalpha() for c in user_query):
            logger.error("Query inválida: muito curta ou sem letras.")
            return False, None

        # Converter a query para minúsculas para facilitar a comparação
        query_lower = user_query.lower()

        # Verificar se contém pelo menos uma palavra-chave de população ou intervenção
        has_population = any(keyword in query_lower for keyword in self.population_keywords)
        has_intervention = any(keyword in query_lower for keyword in self.intervention_keywords)

        if not (has_population or has_intervention):
            logger.error("Query inválida: deve conter pelo menos uma população específica ou uma intervenção.")
            return False, None

        # Se chegou aqui, a query é válida; retornar a query original como "traduzida"
        logger.info(f"Query validada: {user_query}")
        return True, user_query