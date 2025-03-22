# C:\Users\Usuario\Desktop\projetos\PUBMED_CREW\main.py
import os
import logging
from dotenv import load_dotenv
from agents.query_validator import QueryValidator
from agents.pubmed_searcher import PubmedSearcher
from agents.search_refiner import SearchRefiner

load_dotenv()

required_vars = ["ANTHROPIC_API_KEY", "PUBMED_EMAIL"]
for var in required_vars:
    if not os.getenv(var):
        raise ValueError(f"Variável de ambiente {var} não definida no .env")

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

def main():
    user_query = input("Digite sua query: ")
    logger.info(f"Query recebida: {user_query}")
    
    validator = QueryValidator()
    searcher = PubmedSearcher()
    refiner = SearchRefiner()

    is_valid, validated_query = validator.validate_query(user_query)
    if not is_valid:
        logger.error("Query inválida: deve conter população e intervenção.")
        print("A query deve conter pelo menos uma população específica e uma intervenção.")
        return
    logger.info(f"Query validada e traduzida: {validated_query}")

    initial_query = searcher.build_initial_query(validated_query)
    abstracts, pmids = searcher.search_pubmed(initial_query)

    if not pmids:
        logger.warning("Nenhum resultado na busca inicial.")

    current_query = initial_query
    iteration = 0
    max_initial_iterations = 3
    max_additional_iterations = 5
    min_abstracts = 20  # Número mínimo de abstracts desejado

    while True:
        iteration += 1
        logger.info(f"Iteração {iteration} - Query atual: {current_query}")
        refined_query = refiner.refine_search(current_query, abstracts, validated_query)
        logger.info(f"Query refinada: {refined_query}")

        # Verificar se a query não mudou e há resultados suficientes
        if refined_query == current_query and pmids and len(abstracts) >= min_abstracts:
            logger.info("Busca finalizada com resultados suficientes.")
            print(f"Pesquise no PubMed com esta query:\n{refined_query}")
            print("\nResultados encontrados:")
            for pmid, abstract in zip(pmids, abstracts):
                print(f"PMID: {pmid}\nAbstract: {abstract}\n")
            break

        # Verificar limite inicial de iterações
        if iteration > max_initial_iterations:
            if len(abstracts) >= min_abstracts:
                logger.info(f"Limite inicial de iterações atingido, mas número de abstracts suficiente ({len(abstracts)}).")
                print(f"Pesquise no PubMed com esta query:\n{refined_query}")
                print("\nResultados encontrados:")
                for pmid, abstract in zip(pmids, abstracts):
                    print(f"PMID: {pmid}\nAbstract: {abstract}\n")
                break
            else:
                logger.warning(f"Limite inicial de iterações atingido, mas número de abstracts insuficiente ({len(abstracts)}). Tentando mais {max_additional_iterations} iterações.")

        # Verificar limite total de iterações (inicial + adicionais)
        if iteration > (max_initial_iterations + max_additional_iterations):
            logger.warning("Limite total de iterações atingido.")
            print(f"Pesquise no PubMed com esta query (melhor tentativa):\n{refined_query}")
            if pmids:
                print("\nResultados encontrados:")
                for pmid, abstract in zip(pmids, abstracts):
                    print(f"PMID: {pmid}\nAbstract: {abstract}\n")
            break

        current_query = refined_query
        abstracts, pmids = searcher.search_pubmed(current_query)
        logger.info(f"Novos resultados - PMIDs: {pmids}, Abstracts: {len(abstracts)} encontrados")

        # Permitir mais refinamentos na primeira iteração se não houver resultados
        if not pmids and iteration == 1:
            logger.info("Primeira iteração sem resultados; permitindo mais refinamentos.")

if __name__ == "__main__":
    main()