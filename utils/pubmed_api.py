import requests
import xml.etree.ElementTree as ET
import os
import logging

logger = logging.getLogger(__name__)

class PubmedAPI:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.db = "pubmed"
        self.email = os.getenv("PUBMED_EMAIL")
        if not self.email:
            raise ValueError("PUBMED_EMAIL não definida no .env")
        self.headers = {"User-Agent": "PUBMED_CREW/1.0"}

    def esearch(self, query):
        url = f"{self.base_url}esearch.fcgi?db={self.db}&term={query}&retmax=10&retmode=xml&email={self.email}"
        logger.info(f"Enviando esearch URL: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            id_list = [id_elem.text for id_elem in root.findall(".//Id")]
            logger.info(f"PMIDs encontrados: {id_list}")
            return id_list
        except requests.RequestException as e:
            logger.error(f"Erro na busca esearch: {e}")
            return []

    def efetch_abstracts(self, pmids):
        url = f"{self.base_url}efetch.fcgi?db={self.db}&id={','.join(pmids)}&rettype=abstract&retmode=text&email={self.email}"
        logger.info(f"Enviando efetch URL: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            abstracts = response.text.split("\n\n")
            return [abstract.strip() for abstract in abstracts if abstract.strip()]
        except requests.RequestException as e:
            logger.error(f"Erro na busca efetch: {e}")
            return []