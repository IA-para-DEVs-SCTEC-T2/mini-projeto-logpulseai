"""Serviço de análise de logs — orquestra o pipeline completo.

Pipeline: Parser → Analyzer → AIEngine → Repository.
Implementa transação atômica: só persiste se análise completa for bem-sucedida.

Referências: RF-01.5, RF-02.5, RF-06.1
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

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
    Hypothesis,
    LogAnalysisResponse,
    LogEntry,
    LogTemplate,
    SeverityLevel,
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

        # Etapa 3.5: Calcula issues e recommended_actions ANTES de persistir
        temp_response = LogAnalysisResponse.from_full_analysis(
            log_id="temp",  # ID temporário, será substituído
            analysis=analysis,
            diagnosis=diagnosis,
            created_at=datetime.now(UTC),
            entries=entries
        )
        
        # Extrai issues e recommended_actions calculados
        issues = temp_response.issues
        recommended_actions = temp_response.recommended_actions

        # Etapa 4: Persistência (atômica — só persiste se tudo acima passou)
        log_id = await self._persist_result(content, analysis, diagnosis)
        logger.info("Resultado persistido com ID: %s", log_id)

        # Cria resposta final com ID correto
        response = LogAnalysisResponse(
            id=log_id,
            analyzed_at=temp_response.analyzed_at,
            metrics=temp_response.metrics,
            issues=issues,
            recommended_actions=recommended_actions,
            confidence=diagnosis.confidence
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

        Propaga AIEngineError (timeout, indisponível) sem fallback —
        o middleware da API trata esses casos com HTTP 503/504.
        Para erros inesperados, usa diagnóstico heurístico.

        Args:
            analysis: Resultado da análise de anomalias.
            entries: Entradas de log para amostragem.

        Returns:
            Diagnóstico estruturado com hipóteses e sugestões.

        Raises:
            AIEngineError: Se o motor de IA falhar (propagado sem fallback).
        """
        try:
            return self._ai_engine.diagnose(analysis, entries)
        except AIEngineError:
            # Propaga AIEngineError (inclui Timeout e Unavailable) sem fallback
            raise
        except Exception as exc:
            logger.warning("AI diagnosis failed with unexpected error, using fallback: %s", str(exc))
            confidence = self._calculate_fallback_confidence(analysis, entries)
            hypotheses = self._generate_fallback_hypotheses(analysis)
            return AIDiagnosis(
                summary=f"Detectados {analysis.error_count} erros e {analysis.warning_count} warnings",
                probable_cause="Análise automática via IA indisponível - diagnóstico baseado em regras heurísticas",
                hypotheses=hypotheses,
                suggested_fix=f"Analise os {len(analysis.stack_traces)} stack traces detectados e os templates de erro mais frequentes",
                confidence=confidence,
            )

    def _calculate_fallback_confidence(
        self,
        analysis: AnalysisResult,
        entries: list[LogEntry],
    ) -> float:
        """Calcula confidence dinâmico para fallback baseado na qualidade dos dados.
        
        Fatores considerados:
        - Presença de stack traces (mais informação = maior confidence)
        - Quantidade de erros críticos
        - Presença de spikes (padrão claro = maior confidence)
        - Quantidade de templates únicos (mais padrões = menor confidence)
        
        Args:
            analysis: Resultado da análise de anomalias.
            entries: Entradas de log.
            
        Returns:
            Confidence entre 0.3 e 0.7 (nunca igual à IA real que vai de 0.7 a 1.0).
        """
        confidence = 0.5  # Base
        
        # +0.1 se tiver stack traces (mais contexto)
        if len(analysis.stack_traces) > 0:
            confidence += 0.1
        
        # +0.1 se tiver erros críticos (problema claro)
        critical_count = analysis.severity_distribution.get(SeverityLevel.CRITICAL, 0)
        if critical_count > 0:
            confidence += 0.1
        
        # +0.05 se tiver spikes (padrão temporal claro)
        if len(analysis.spikes) > 0:
            confidence += 0.05
        
        # -0.1 se tiver muitos templates únicos (problema difuso)
        if len(analysis.templates) > 10:
            confidence -= 0.1
        
        # -0.05 se tiver poucos erros (menos dados)
        if analysis.error_count < 5:
            confidence -= 0.05
        
        # Garante que fica entre 0.3 e 0.7
        return max(0.3, min(0.7, confidence))
    
    def _generate_fallback_hypotheses(self, analysis: AnalysisResult) -> list:
        """Gera hipóteses baseadas em regras heurísticas.

        Garante sempre exatamente 3 hipóteses para satisfazer o schema AIDiagnosis.

        Args:
            analysis: Resultado da análise de anomalias.

        Returns:
            Lista de Hypothesis com exatamente 3 itens.
        """
        hypotheses = []

        # Hipótese 1: Baseada em spikes
        if analysis.spikes:
            hypotheses.append(Hypothesis(
                description=f"Spike de {analysis.spikes[0].error_count} erros detectado em janela de tempo específica",
                probability="alta",
                action="Investigar eventos ou deploys que ocorreram no período do spike",
            ))
        else:
            hypotheses.append(Hypothesis(
                description="Erros distribuídos ao longo do tempo sem padrão de spike",
                probability="média",
                action="Revisar logs de erro e stack traces para identificar padrão comum",
            ))

        # Hipótese 2: Baseada em stack traces
        if len(analysis.stack_traces) > 0:
            hypotheses.append(Hypothesis(
                description=f"Detectados {len(analysis.stack_traces)} stack traces indicando exceções não tratadas",
                probability="alta",
                action="Analisar stack traces para identificar classes e métodos problemáticos",
            ))
        else:
            hypotheses.append(Hypothesis(
                description="Possível problema de configuração, conectividade ou dependência externa",
                probability="baixa",
                action="Verificar configurações do sistema e status de serviços externos",
            ))

        # Hipótese 3: Baseada em templates ou genérica
        if analysis.templates:
            top_template = analysis.templates[0]
            hypotheses.append(Hypothesis(
                description=f"Padrão de erro mais frequente: '{top_template.pattern}' ({top_template.occurrences} ocorrências)",
                probability="média",
                action="Focar na resolução deste padrão de erro mais comum",
            ))
        else:
            hypotheses.append(Hypothesis(
                description="Ausência de padrões claros pode indicar erros esporádicos ou intermitentes",
                probability="baixa",
                action="Monitorar o sistema por mais tempo para identificar padrão recorrente",
            ))

        return hypotheses  # Sempre 3 hipóteses
    
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
