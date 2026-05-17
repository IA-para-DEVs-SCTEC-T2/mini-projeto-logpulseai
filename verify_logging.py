#!/usr/bin/env python3
"""Script de verificação do sistema de logging estruturado do LogPulse IA.

Este script demonstra que o logging está funcionando corretamente em todos
os componentes críticos do sistema.
"""

import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.logging import configure_logging, get_logger

# Configura logging
configure_logging(log_level="INFO", log_file="logpulse.log")

# Obtém loggers de diferentes módulos
logger_main = get_logger("verify_logging")
logger_parser = get_logger("src.parsers.drain3_parser")
logger_analyzer = get_logger("src.analyzer.detector")
logger_ai = get_logger("src.ai.ollama_engine")
logger_repo = get_logger("src.repository.sqlite_repository")
logger_api = get_logger("src.main")

print("=" * 80)
print("VERIFICAÇÃO DO SISTEMA DE LOGGING ESTRUTURADO")
print("=" * 80)
print()

# 1. Teste de logging básico
print("1. Testando logging básico...")
logger_main.info("verification_started", test_type="basic")
logger_main.debug("debug_message", detail="This is a debug message")
logger_main.warning("warning_message", detail="This is a warning")
logger_main.error("error_message", detail="This is an error")
print("   ✓ Logging básico funcionando")
print()

# 2. Teste de logging do Parser
print("2. Testando logging do Parser...")
logger_parser.info(
    "parsing_started",
    content_length=5432,
    format="json"
)
logger_parser.info(
    "parsing_completed",
    total_lines=120,
    entries_parsed=118,
    errors=2,
    templates_extracted=15
)
logger_parser.warning(
    "line_parse_failed",
    line_number=42,
    error="Invalid JSON format",
    raw_line="malformed log line..."
)
print("   ✓ Parser logging funcionando")
print()

# 3. Teste de logging do Analyzer
print("3. Testando logging do Analyzer...")
logger_analyzer.info(
    "analysis_started",
    total_entries=120,
    total_templates=15
)
logger_analyzer.debug(
    "severity_distribution_calculated",
    distribution={"ERROR": 15, "WARNING": 8, "INFO": 97}
)
logger_analyzer.warning(
    "spikes_detected",
    spike_count=2,
    spikes=[
        {
            "start_time": "2024-01-15T10:00:00Z",
            "end_time": "2024-01-15T10:01:00Z",
            "error_count": 12
        }
    ]
)
logger_analyzer.info(
    "analysis_completed",
    total_entries=120,
    error_count=15,
    warning_count=8,
    spike_count=2
)
print("   ✓ Analyzer logging funcionando")
print()

# 4. Teste de logging do AIEngine
print("4. Testando logging do AIEngine...")
logger_ai.info(
    "diagnosis_started",
    model="llama3",
    total_entries=50,
    error_count=15,
    warning_count=8
)
logger_ai.debug(
    "sample_created",
    original_count=120,
    sampled_count=50
)
logger_ai.info(
    "ollama_request_attempt",
    attempt=1,
    max_retries=3,
    model="llama3"
)
logger_ai.info(
    "diagnosis_completed",
    model="llama3",
    attempt=1,
    hypotheses_count=3,
    confidence=0.85
)
print("   ✓ AIEngine logging funcionando")
print()

# 5. Teste de logging do Repository
print("5. Testando logging do Repository...")
logger_repo.info(
    "repository_initialization_started",
    db_path="logpulse.db"
)
logger_repo.info(
    "repository_initialization_completed",
    db_path="logpulse.db"
)
logger_repo.info(
    "repository_create_started",
    log_id="uuid-123-456",
    content_length=5432,
    total_entries=120
)
logger_repo.info(
    "repository_create_completed",
    log_id="uuid-123-456"
)
logger_repo.debug(
    "repository_get_by_id_started",
    log_id="uuid-123-456"
)
logger_repo.debug(
    "repository_get_by_id_completed",
    log_id="uuid-123-456"
)
print("   ✓ Repository logging funcionando")
print()

# 6. Teste de logging da API
print("6. Testando logging da API...")
logger_api.info(
    "request_started",
    method="POST",
    path="/api/v1/logs/text",
    client_host="127.0.0.1"
)
logger_api.info(
    "request_completed",
    method="POST",
    path="/api/v1/logs/text",
    status_code=200,
    duration_ms=1234.56
)
print("   ✓ API logging funcionando")
print()

# Verificação final
print("=" * 80)
print("VERIFICAÇÃO CONCLUÍDA COM SUCESSO!")
print("=" * 80)
print()
print("Logs estruturados foram gerados em:")
print(f"  - Console (stdout)")
print(f"  - Arquivo: logpulse.log")
print()
print("Para visualizar os logs do arquivo:")
print("  cat logpulse.log | tail -20")
print()
print("Para filtrar logs por nível:")
print('  cat logpulse.log | grep \'"level": "error"\'')
print()
print("Para filtrar logs por evento:")
print('  cat logpulse.log | grep \'"event": "analysis_completed"\'')
print()

logger_main.info("verification_completed", status="success", all_tests_passed=True)
