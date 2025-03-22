from utils.pubmed_api import PubmedAPI
import logging

logger = logging.getLogger(__name__)

class PubmedSearcher:
    def __init__(self):
        self.api = PubmedAPI()

    def build_initial_query(self, validated_query):
        terms = validated_query.split()
        key_terms = [term for term in terms if len(term) > 3 and term not in ["for", "in", "with", "and"]]
        query = " ".join(key_terms[:3])
        logger.info(f"Query inicial construída: {query}")
        return query

    def search_pubmed(self, query):
        pmids = self.api.esearch(query)
        if not pmids:
            logger.warning(f"Nenhum PMID encontrado para a query: {query}")
            return [], []
        abstracts = self.api.efetch_abstracts(pmids)
        if not abstracts:
            logger.warning(f"Nenhum abstract retornado para PMIDs: {pmids}")
        return abstracts, pmids