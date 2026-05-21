"""Parser de logs concreto usando Drain3 para extração de templates."""

from __future__ import annotations

import json
import re

from drain3 import TemplateMiner  # type: ignore[import-untyped]
from drain3.template_miner_config import TemplateMinerConfig  # type: ignore[import-untyped]

from src.core.logging import get_logger
from src.models.schemas import LogEntry, LogTemplate, SeverityLevel
from src.parsers.base import LogParser
from src.parsers.normalizer import (
    extract_timestamp_from_line,
    normalize_severity,
    parse_timestamp,
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Regex para detecção de formato
# ---------------------------------------------------------------------------

# Syslog RFC 3164: "Jan 15 10:00:00 hostname app[pid]: message"
_RE_SYSLOG = re.compile(
    r"^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}"
    r"\s+\S+\s+\S+:\s+(.+)$"
)

# Nível de severidade em texto livre: [ERROR], ERROR:, (WARNING), etc.
_RE_LEVEL_IN_LINE = re.compile(
    r"\b(TRACE|DEBUG|INFO|INFORMATION|WARN|WARNING|ERR|ERROR|FATAL|CRITICAL|CRIT)\b",
    re.IGNORECASE,
)

# Máximo de sample_messages por template
_MAX_SAMPLES = 5

# Configuração do Drain3
_DRAIN_DEPTH = 4
_DRAIN_SIM_TH = 0.4


def _build_drain_config() -> TemplateMinerConfig:
    """Cria configuração do Drain3 com parâmetros do projeto."""
    config = TemplateMinerConfig()
    config.drain_depth = _DRAIN_DEPTH
    config.drain_sim_th = _DRAIN_SIM_TH
    config.drain_max_children = 100
    config.parametrize_numeric_tokens = True
    return config


class Drain3LogParser(LogParser):
    """Parser de logs usando Drain3 para extração de templates.

    Suporta três formatos de entrada:
    - JSON estruturado: {"timestamp": ..., "level": ..., "message": ...}
    - Syslog RFC 3164: Jan 15 10:00:00 host app[pid]: message
    - Texto livre: qualquer outro formato (fallback)

    Normaliza aliases de severidade e infere timestamp/level quando ausentes.
    """

    def __init__(self) -> None:
        """Inicializa o parser com Drain3 configurado."""
        config = _build_drain_config()
        self._miner = TemplateMiner(config=config)
        # template_id → {"pattern": str, "occurrences": int, "samples": list[str]}
        self._templates: dict[str, dict[str, object]] = {}

    # ------------------------------------------------------------------
    # Interface pública
    # ------------------------------------------------------------------

    def parse(self, raw_content: str) -> list[LogEntry]:
        """Transforma conteúdo bruto de log em lista de LogEntry.

        Args:
            raw_content: Conteúdo completo do arquivo ou texto de log.

        Returns:
            Lista de LogEntry normalizadas. Linhas malformadas são
            ignoradas sem interromper o processamento.
        """
        logger.info("Iniciando parsing de log", content_length=len(raw_content))
        
        entries: list[LogEntry] = []
        lines = raw_content.splitlines()
        total_lines = len(lines)
        errors = 0
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = self._parse_line(line)
                if entry is not None:
                    entries.append(entry)
            except Exception as exc:
                # Linha malformada: registra e continua (RNF-03)
                errors += 1
                logger.warning(
                    "Falha ao parsear linha",
                    line_number=line_num,
                    error=str(exc),
                    raw_line=line[:100]  # Limita tamanho do log
                )
                continue
        
        logger.info(
            "Parsing concluído",
            total_lines=total_lines,
            entries_parsed=len(entries),
            errors=errors,
            templates_extracted=len(self._templates)
        )
        
        return entries

    def get_templates(self) -> list[LogTemplate]:
        """Retorna os templates extraídos pelo Drain3 até o momento.

        Returns:
            Lista de LogTemplate com pattern, occurrences e sample_messages.
        """
        result: list[LogTemplate] = []
        for tmpl_id, data in self._templates.items():
            samples: list[str] = data.get("samples", [])  # type: ignore[assignment]
            result.append(
                LogTemplate(
                    template_id=tmpl_id,

                    pattern=str(data.get("pattern", "")),
                    occurrences=int(str(data.get("occurrences", 0))),
                    sample_messages=samples,
                )
            )
        return result

    # ------------------------------------------------------------------
    # Detecção de formato
    # ------------------------------------------------------------------

    def _parse_line(self, line: str) -> LogEntry | None:
        """Detecta o formato da linha e delega ao parser correto."""
        # Tenta JSON primeiro
        if line.startswith("{"):
            entry = self._parse_json(line)
            if entry is not None:
                return entry

        # Tenta Syslog RFC 3164
        if _RE_SYSLOG.match(line):
            return self._parse_syslog(line)

        # Fallback: texto livre
        return self._parse_plaintext(line)

    # ------------------------------------------------------------------
    # Parsers por formato
    # ------------------------------------------------------------------

    def _parse_json(self, line: str) -> LogEntry | None:
        """Parseia linha no formato JSON estruturado."""
        try:
            data = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            return None

        if not isinstance(data, dict):
            return None

        # Extrai campos — suporta variações de chave
        raw_ts = (
            data.get("timestamp") or data.get("time") or data.get("ts") or data.get("@timestamp")
        )
        raw_level = (
            data.get("level") or data.get("severity") or data.get("lvl") or data.get("log_level")
        )
        message = str(data.get("message") or data.get("msg") or data.get("text") or "")

        ts, ts_inferred = parse_timestamp(str(raw_ts) if raw_ts else None)
        level, level_inferred = normalize_severity(str(raw_level) if raw_level else None)

        if not message:
            message = line

        template_id = self._process_template(message)

        return LogEntry(
            raw_content=line,
            template_id=template_id,
            severity=level,
            timestamp=ts,
            message=message,
            level_inferred=level_inferred,
            timestamp_inferred=ts_inferred,
        )

    def _parse_syslog(self, line: str) -> LogEntry:
        """Parseia linha no formato Syslog RFC 3164."""
        # Extrai timestamp (primeiros 3 tokens: "Jan 15 10:00:00")
        parts = line.split(None, 4)
        ts_str = " ".join(parts[:3]) if len(parts) >= 3 else None
        ts, ts_inferred = parse_timestamp(ts_str)

        # Mensagem é o restante após "host app[pid]: "
        message = parts[4] if len(parts) >= 5 else line

        # Tenta extrair nível da mensagem
        level, level_inferred = _extract_level_from_text(message)

        template_id = self._process_template(message)

        return LogEntry(
            raw_content=line,
            template_id=template_id,
            severity=level,
            timestamp=ts,
            message=message,
            level_inferred=level_inferred,
            timestamp_inferred=ts_inferred,
        )

    def _parse_plaintext(self, line: str) -> LogEntry:
        """Parseia linha de texto livre (fallback genérico)."""
        ts, ts_inferred, remaining = extract_timestamp_from_line(line)
        level, level_inferred = _extract_level_from_text(remaining)

        # Remove o token de nível da mensagem para ficar mais limpa
        message = _RE_LEVEL_IN_LINE.sub("", remaining).strip(" :-[]()") or line

        template_id = self._process_template(message)

        return LogEntry(
            raw_content=line,
            template_id=template_id,
            severity=level,
            timestamp=ts,
            message=message,
            level_inferred=level_inferred,
            timestamp_inferred=ts_inferred,
        )

    # ------------------------------------------------------------------
    # Integração com Drain3
    # ------------------------------------------------------------------

    def _process_template(self, message: str) -> str:
        """Processa mensagem no Drain3 e atualiza cache de templates.

        Args:
            message: Mensagem de log a ser agrupada.

        Returns:
            ID do template associado à mensagem.
        """
        result = self._miner.add_log_message(message)
        # Drain3 >= 0.9: retorna dict com cluster_id e template_mined
        template_id = str(result.get("cluster_id", ""))
        pattern = str(result.get("template_mined", ""))

        if template_id not in self._templates:
            self._templates[template_id] = {
                "pattern": pattern,
                "occurrences": 0,
                "samples": [],
            }

        # Atualiza pattern (pode mudar conforme Drain3 aprende)
        self._templates[template_id]["pattern"] = pattern

        # Incrementa contagem
        count = int(str(self._templates[template_id].get("occurrences", 0)))
        self._templates[template_id]["occurrences"] = count + 1

        # Coleta até 5 amostras
        samples: list[str] = self._templates[template_id].get("samples", [])  # type: ignore[assignment]
        if len(samples) < _MAX_SAMPLES:
            samples.append(message)
            self._templates[template_id]["samples"] = samples

        return template_id


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_level_from_text(text: str) -> tuple[SeverityLevel, bool]:
    """Extrai nível de severidade de uma string de texto livre.

    Args:
        text: Texto onde buscar o nível.

    Returns:
        Tupla (SeverityLevel, inferred: bool).
    """
    m = _RE_LEVEL_IN_LINE.search(text)
    if m:
        level, inferred = normalize_severity(m.group())
        return level, inferred
    return SeverityLevel.INFO, True
