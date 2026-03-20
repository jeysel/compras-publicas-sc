import abc
import os
import json
from datetime import datetime
from src.utils.logger import Logger


class BaseSource(abc.ABC):
    """
    Classe base para todas as fontes de dados do pipeline de Compras Públicas.
    Define o contrato mínimo que cada fonte deve implementar.
    """

    def __init__(self, config: dict):
        self.config = config
        self.logger = Logger().get_logger(self.__class__.__name__)
        self.raw_path = config["output"]["raw_path"]

    # ------------------------------
    # Métodos obrigatórios
    # ------------------------------

    @abc.abstractmethod
    def authenticate(self):
        """Realiza autenticação (se necessário)."""
        pass

    @abc.abstractmethod
    def fetch_data(self):
        """Busca os dados brutos da fonte."""
        pass

    @abc.abstractmethod
    def normalize(self, raw_data):
        """Normaliza o formato bruto para um formato padronizado."""
        pass

    # ------------------------------
    # Métodos utilitários
    # ------------------------------

    def save_raw(self, data, filename_prefix="data"):
        """Salva dados brutos em /data/raw com timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.json"

        os.makedirs(self.raw_path, exist_ok=True)
        filepath = os.path.join(self.raw_path, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Arquivo salvo: {filepath}")
        return filepath

    def validate_response(self, response):
        """Valida se a resposta da fonte é válida."""
        if not response:
            raise ValueError("Resposta vazia da fonte.")
        return True

    def run(self):
        """Fluxo completo da fonte."""
        self.logger.info("Iniciando ingestão da fonte...")

        self.authenticate()
        raw_data = self.fetch_data()
        self.validate_response(raw_data)
        normalized = self.normalize(raw_data)
        self.save_raw(normalized)

        self.logger.info("Ingestão concluída com sucesso.")