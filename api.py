from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from dotenv import load_dotenv
import os
from agents.query_validator import QueryValidator
from agents.pubmed_searcher import PubmedSearcher
from agents.search_refiner import SearchRefiner

load_dotenv()

# Verificar variáveis de ambiente
required_vars = ["ANTHROPIC_API_KEY", "PUBMED_EMAIL"]
for var in required_vars:
    if not os.getenv(var):
        raise ValueError(f"Variável de ambiente {var} não definida no .env")

# Configurar logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Definir o modelo de entrada usando Pydantic
class SearchRequest(BaseModel):
    picott_text: str
    max_iterations: int = 3

# Inicializar o FastAPI
app = FastAPI()

@app.post("/api/search")
async def search_pubmed(request: SearchRequest):
    user_query = request.picott_text
    max_initial_iterations = request.max_iterations
    logger.info(f"Query recebida: {user_query}, Max iterações: {max_initial_iterations}")

    try:
        validator = QueryValidator()
        searcher = PubmedSearcher()
        refiner = SearchRefiner()

        is_valid, validated_query = validator.validate_query(user_query)
        if not is_valid:
            logger.error("Query inválida: deve conter população e intervenção.")
            raise HTTPException(status_code=400, detail="A query deve conter pelo menos uma população específica e uma intervenção.")
        logger.info(f"Query validada e traduzida: {validated_query}")

        initial_query = searcher.build_initial_query(validated_query)
        abstracts, pmids = searcher.search_pubmed(initial_query)

        if not pmids:
            logger.warning("Nenhum resultado na busca inicial.")

        current_query = initial_query
        iteration = 0
        max_additional_iterations = 5
        min_abstracts = 20

        while True:
            iteration += 1
            logger.info(f"Iteração {iteration} - Query atual: {current_query}")
            refined_query = refiner.refine_search(current_query, abstracts, validated_query)
            logger.info(f"Query refinada: {refined_query}")

            if refined_query == current_query and pmids and len(abstracts) >= min_abstracts:
                logger.info("Busca finalizada com resultados suficientes.")
                break

            if iteration > max_initial_iterations:
                if len(abstracts) >= min_abstracts:
                    logger.info(f"Limite inicial de iterações atingido, mas número de abstracts suficiente ({len(abstracts)}).")
                    break
                else:
                    logger.warning(f"Limite inicial de iterações atingido, mas número de abstracts insuficiente ({len(abstracts)}). Tentando mais {max_additional_iterations} iterações.")

            if iteration > (max_initial_iterations + max_additional_iterations):
                logger.warning("Limite total de iterações atingido.")
                break

            current_query = refined_query
            abstracts, pmids = searcher.search_pubmed(current_query)
            logger.info(f"Novos resultados - PMIDs: {pmids}, Abstracts: {len(abstracts)} encontrados")

            if not pmids and iteration == 1:
                logger.info("Primeira iteração sem resultados; permitindo mais refinamentos.")

        # Preparar a resposta
        results = [{"pmid": pmid, "abstract": abstract} for pmid, abstract in zip(pmids, abstracts)]
        return {
            "query": refined_query,
            "results": results,
            "total_results": len(results)
        }

    except Exception as e:
        logger.error(f"Erro durante a busca: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro durante a busca: {str(e)}")
        