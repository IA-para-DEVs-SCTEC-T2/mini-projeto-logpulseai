"""Serviço de análise de logs — orquestra o pipeline completo.

Pipeline: Parser → Analyzer → AIEngine → Repository.
Implementa transação atômica: só persiste se análise completa for bem-sucedida.

Referências: RF-01.5, RF-02.5, RF-06.1
"""

from __future__ import annotations

import logging

from src.ai.base import AIEngine
from src.analyzer.base import LogAnalyzer
from src.exceptions import (
    AIEngineError,
    AnalysisError,
    LogPulseError,
    ParsingError,
    StorageError,
)
from src.models.schemas import (
    AIDiagnosis,
    AnalysisResult,
    LogAnalysisResponse,
    LogEntry,
    LogTemplate,
)
from src.parsers.base import LogParser
from src.repository.base import LogRepository

logger = logging.getLogger(__name__)


class LogAnalysisService:
    """Serviço que orquestra o pipeline completo de análise de logs.

    Coordena a execução sequencial de:
    1. Parsing do conteúdo bruto (Parser)
    2. Análise de anomalias (Analyzer)
    3. Diagnóstico inteligente (AIEngine)
    4. Persistência do resultado (Repository)

    A operação é atômica: só persiste se todas as etapas forem bem-sucedidas.

    Args:
        parser: Implementação de LogParser para parsing do conteúdo.
        analyzer: Implementação de LogAnalyzer para detecção de anomalias.
        ai_engine: Implementação de AIEngine para diagnóstico IA.
        repository: Implementação de LogRepository para persistência.

    Example:
        >>> service = LogAnalysisService(parser, analyzer, engine, repo)
        >>> response = await service.analyze_content("2024-01-15 ERROR: timeout")
        >>> print(response.diagnosis.summary)
    """

    def __init__(
        self,
        parser: LogParser,
        analyzer: LogAnalyzer,
        ai_engine: AIEngine,
        repository: LogRepository,
    ) -> None:
        """Inicializa o serviço com as dependências injetadas."""
        self._parser = parser
        self._analyzer = analyzer
        self._ai_engine = ai_engine
        self._repository = repository

    async def analyze_content(self, content: str) -> LogAnalysisResponse:
        """Orquestra o pipeline completo de análise de logs.

        Executa sequencialmente: Parser → Analyzer → AIEngine → Repository.
        Transação atômica: só persiste se análise completa for bem-sucedida.

        Args:
            content: Conteúdo bruto do log (texto ou conteúdo de arquivo).

        Returns:
            LogAnalysisResponse com análise, diagnóstico e metadados.

        Raises:
            ParsingError: Se o parser não conseguir processar o conteúdo.
            AnalysisError: Se o analyzer encontrar estado inválido.
            AIEngineError: Se o motor de IA falhar (timeout, indisponível).
            StorageError: Se a persistência falhar.
        """
        logger.info("Iniciando pipeline de análise de logs")

        # Etapa 1: Parsing
        entries = self._parse_content(content)
        logger.info("Parsing concluído: %d entradas extraídas", len(entries))

        # Etapa 2: Análise de anomalias
        templates = self._parser.get_templates()
        analysis = self._analyze_entries(entries, templates)
        logger.info(
            "Análise concluída: %d erros, %d warnings, %d spikes",
            analysis.error_count,
            analysis.warning_count,
            len(analysis.spikes),
        )

        # Etapa 3: Diagnóstico IA
        diagnosis = self._generate_diagnosis(analysis, entries)
        logger.info("Diagnóstico gerado: confiança %.2f", diagnosis.confidence)

        # Etapa 4: Persistência (atômica — só persiste se tudo acima passou)
        log_id = await self._persist_result(content, analysis, diagnosis)
        logger.info("Resultado persistido com ID: %s", log_id)

        # Recupera o registro completo para retorno
        response = await self._repository.get_by_id(log_id)
        if response is None:
            raise StorageError(
                f"Falha ao recuperar registro recém-criado: {log_id}"
            )

        return response

    def _parse_content(self, content: str) -> list[LogEntry]:
        """Executa parsing do conteúdo bruto.

        Args:
            content: Conteúdo bruto do log.

        Returns:
            Lista de LogEntry normalizadas.

        Raises:
            ParsingError: Se o conteúdo não puder ser parseado.
        """
        try:
            entries = self._parser.parse(content)
        except Exception as exc:
            raise ParsingError(
                f"Falha ao parsear conteúdo de log: {exc}"
            ) from exc

        if not entries:
            raise ParsingError(
                "Nenhuma entrada de log válida encontrada no conteúdo fornecido"
            )

        return entries

    def _analyze_entries(
        self,
        entries: list[LogEntry],
        templates: list[LogTemplate],
    ) -> AnalysisResult:
        """Executa análise de anomalias nas entradas.

        Args:
            entries: Lista de entradas de log normalizadas.
            templates: Templates extraídos pelo parser.

        Returns:
            Resultado da análise de anomalias.

        Raises:
            AnalysisError: Se a análise falhar.
        """
        try:
            return self._analyzer.analyze(entries, templates)
        except LogPulseError:
            raise
        except Exception as exc:
            raise AnalysisError(
                f"Falha durante análise de anomalias: {exc}"
            ) from exc

    def _generate_diagnosis(
        self,
        analysis: AnalysisResult,
        entries: list[LogEntry],
    ) -> AIDiagnosis:
        """Gera diagnóstico inteligente via motor de IA.

        Args:
            analysis: Resultado da análise de anomalias.
            entries: Entradas de log para amostragem.

        Returns:
            Diagnóstico estruturado com hipóteses e sugestões.

        Raises:
            AIEngineError: Se o motor de IA falhar.
        """
        try:
            return self._ai_engine.diagnose(analysis, entries)
        except AIEngineError:
            raise
        except Exception as exc:
            raise AIEngineError(
                f"Falha ao gerar diagnóstico IA: {exc}"
            ) from exc

    async def _persist_result(
        self,
        content: str,
        analysis: AnalysisResult,
        diagnosis: AIDiagnosis,
    ) -> str:
        """Persiste o resultado da análise no repositório.

        Args:
            content: Conteúdo bruto original.
            analysis: Resultado da análise.
            diagnosis: Diagnóstico gerado.

        Returns:
            UUID do registro criado.

        Raises:
            StorageError: Se a persistência falhar.
        """
        try:
            return await self._repository.create(content, analysis, diagnosis)
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError(
                f"Falha ao persistir resultado da análise: {exc}"
            ) from exc
