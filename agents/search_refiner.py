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
        - Aplique o princípio do mínimo: evite combinar termos como "vagus nerve stimulation" e "auricular vagus nerve stimulation"  --> aqui bastaria "vagus nerve stimulation"
        - Evite ao máximo expressões com mais de 2 termos - pense antes se o termo é necessário.
        - Adicione aspectos de outcome específicos EM OUTRO PARENTESE (LIGADO PELO "AND") SOMENTE SE MAIS DE 500 RESULTADOS FOREM IDENTIFICADOS, evitando "OR", "HR", e sim outcomes ou comparadores extremamente específicos IDENTIFICADOS na query inicial do usuário.
        - Exemplo de outcomes: "progression-free survival", "survival", "cerebral vasospasm", evitando termos genéricos como "inflammation" isoladamente; use "OR" entre eles dentro do parêntese.
        - Use aspas apenas em termos compostos essenciais (ex.: "vagus nerve stimulation"); todos os termos devem estar entre aspas ou com wildcard (ex.: "migrain*").
        - Não inclua tipos de estudos de início  (ex.: "randomized controlled trial"), anos, "humans", "animals" ou filtros semelhantes.
        - Você estará permitido a usar filtros como SOMENTE SE FOREM ENCONTRADOS MAIS DE 300 RESULTADOS OU SE O USUÁRIO TE SOLICITAR MUITO EXPLICITAMENTE, DIZENDO QUE NÃO QUER OUTRO TIPO!


        # COHORT: ((“prospective cohort”[ti] OR “relative risk*”[tiab] OR“prospective”[ti] OR “cohort study”[ti] OR longitudinal[ti] OR “long-term”[ti] OR “RR”[tiab] OR “RRs”[tiab] OR ) NOT ("systematic review"[ti] OR "meta-analysis"[ti] OR "metaanalysis"[ti] OR "metanalysis"[ti] OR “phase 1” OR “phase 2” OR “phase 3” OR “pilot trial” OR “retrospective cohort” OR "network"[ti]))
        # Case-control: (("case-control"[ti] OR "case control"[ti] OR "retrospective study"[ti] OR “retrospective cohort”[tiab] OR "matched study"[ti]) AND ("odds ratio"[tiab] OR "odds ratios"[tiab] OR "case referent"[tiab] OR "unmatched"[tiab] OR "matched pairs"[tiab] OR "risk factor"[tiab]) NOT ("systematic review"[ti] OR "meta-analysis"[ti] OR "metaanalysis"[ti] OR "metanalysis"[ti] OR "network"[ti]))
        # SYSTEMATIC REVIEW OR META-ANALYSIS: ("systematic review"[ti] OR "meta-analysis"[ti] OR "metaanalysis"[ti] OR "metanalysis"[ti] OR "network"[ti]) 
        # RCT: (("controlled trial"[ti] OR "clinical trial"[ti] OR randomized[ti] OR placebo[ti] OR double-blind[ti] OR controlled[ti] OR randomised[ti] OR RCT[ti]) NOT ("systematic review"[ti] OR "protocol"[ti] OR "data from"[ti] OR "results from"[ti] OR "post-hoc" OR "case-controlled"[ti] OR "meta-analysis"[ti] OR "metaanalysis"[ti] OR comment*[ti] OR guidelin*[ti] OR "a review"[ti] OR "metanalysis"[ti] OR "case series"[ti]))


        - Se encontrar menos de 20 resultados, simplifique a query removendo termos menos relevantes, mantendo o núcleo da população e intervenção.
        - Retorne APENAS a query refinada, no formato exato para pesquisa no PubMed, sem explicações ou texto adicional.
        - Garanta que não seja retornados [All fields], [mh], mesh etc., [tiab] - REMOVER TUDO!
        - Garantir o máximo de sinônimos relevantes! 
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