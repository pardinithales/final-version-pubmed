from anthropic import Anthropic
import logging
import re
import random
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class SearchRefiner:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-3-7-sonnet-20250219"

    def extract_terms_from_abstracts(self, abstracts):
        if not abstracts:
            return set()
        num_abstracts = min(random.randint(1, 5), len(abstracts))
        selected_abstracts = random.sample(abstracts, num_abstracts)
        terms = set()
        for abstract in selected_abstracts:
            siglas = re.findall(r'\b[A-Z]{2,}\b', abstract)
            terms.update(siglas)
            words = re.findall(r'\b\w{4,}\b', abstract.lower())
            frequent_terms = [word for word in set(words) if words.count(word) > 1 and word not in ["with", "from", "this", "study", "patients"]]
            terms.update(frequent_terms[:2])
        return terms

    def refine_search(self, current_query, abstracts, original_query):
        prompt = f"""
        Query original do usuário: "{original_query}"
        Query atual no PubMed: "{current_query}"
        Abstracts retornados (amostra): {abstracts[:3] if abstracts else 'Nenhum resultado encontrado'}
        Refine a query para ser usada diretamente no PubMed:
        - Considere a população e a intervenção da query original como base.
        - Use os abstracts para identificar siglas (ex.: "SAH" para "subarachnoid hemorrhage") ou sinônimos relevantes, adicionando-os com "OR" apenas se não forem redundantes.
        - Use os abstracts para extrair ao máximo nomes de dispositivos (ex.: "taVNS") e nomes comerciais de medicações (ex.: "apixaban"), adicionando-os com "OR" se relevantes.
        - Evite redundâncias: por exemplo, use "stroke" em vez de "acute stroke" e "stroke"; para "migraine" ou "migrainous", use "migrain*" se aplicável.
        - Aplique o princípio do mínimo: evite combinar termos como "vagus nerve stimulation" e "auricular vagus nerve stimulation" (use apenas o mais abrangente).
        - Adicione aspectos de outcome específicos EM OUTRO PARENTESE (LIGADO PELO "AND") SOMENTE SE MAIS DE 500 RESULTADOS FOREM IDENTIFICADOS, evitando "OR", "HR", e sim outcomes ou comparadores extremamente específicos IDENTIFICADOS na query inicial do usuário.
        - Exemplo de outcomes: "progression-free survival", "survival", "cerebral vasospasm", evitando termos genéricos como "inflammation" isoladamente; use "OR" entre eles dentro do parêntese.
        - Use aspas apenas em termos compostos essenciais (ex.: "vagus nerve stimulation"); todos os termos devem estar entre aspas ou com wildcard (ex.: "migrain*").
        - Não inclua tipos de estudo (ex.: "randomized controlled trial"), anos, "humans" ou filtros semelhantes.
        - Se encontrar menos de 20 resultados, simplifique a query removendo termos menos relevantes, mantendo o núcleo da população e intervenção.
        - Retorne APENAS a query refinada, no formato exato para pesquisa no PubMed, sem explicações ou texto adicional.
        """
        if abstracts:
            extra_terms = self.extract_terms_from_abstracts(abstracts)
            prompt += f"\nTermos extraídos dos abstracts (priorize especificidade, inclua dispositivos e medicações): {', '.join(extra_terms)}"
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            temperature=0.8,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        refined_query = message.content[0].text.strip()
        logger.debug(f"Query refinada gerada: {refined_query}")
        return refined_query