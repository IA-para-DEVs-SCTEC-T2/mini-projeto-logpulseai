"""Ponto de entrada da CLI do LogPulse IA."""

from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path
from typing import Optional

import orjson
import typer
from rich.console import Console
from rich.table import Table

from logpulse import __version__
from logpulse.ai.engine import AIEngine
from logpulse.analyzer.engine import Analyzer
from logpulse.config import load_config
from logpulse.models import AnalysisResult, SeverityLevel
from logpulse.parsers.auto import AutoParser
from logpulse.parsers.json_parser import JsonParser
from logpulse.parsers.plaintext_parser import PlaintextParser
from logpulse.parsers.syslog_parser import SyslogParser
from logpulse.sources.file_source import FileSource
from logpulse.sources.stdin_source import StdinSource

app = typer.Typer(
    name="logpulse",
    help="LogPulse IA — Análise inteligente de logs.",
    add_completion=False,
)
console = Console()


class OutputFormat(str, Enum):
    """Formato de saída da análise."""

    text = "text"
    json = "json"


class ParserFormat(str, Enum):
    """Formato do parser de logs."""

    auto = "auto"
    json = "json"
    plaintext = "plaintext"
    syslog = "syslog"


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"logpulse {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(  # noqa: UP007
        None, "--version", "-v", callback=version_callback, is_eager=True, help="Exibe a versão."
    ),
) -> None:
    """LogPulse IA — Investigue problemas rapidamente através dos seus logs."""


@app.command()
def analyze(
    source: str = typer.Argument(..., help="Arquivo de log ou '-' para stdin."),
    ai: bool = typer.Option(False, "--ai", help="Ativa diagnóstico com IA."),
    follow: bool = typer.Option(False, "--follow", "-f", help="Monitoramento contínuo (tail -f)."),
    output: OutputFormat = typer.Option(OutputFormat.text, "--output", "-o", help="Formato de saída."),
    format: ParserFormat = typer.Option(ParserFormat.auto, "--format", help="Formato do parser."),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Caminho para logpulse.toml."),  # noqa: UP007
) -> None:
    """Analisa logs de um arquivo ou stdin."""
    cfg = load_config(config)

    # Seleciona parser
    fmt = format.value if format != ParserFormat.auto else (cfg.get("parser", {}) or {}).get("format", "auto")  # type: ignore[union-attr]
    parser = _get_parser(str(fmt))

    # Seleciona fonte
    if source == "-":
        log_source = StdinSource()
        source_name = "stdin"
    else:
        path = Path(source)
        if not path.exists():
            console.print(f"[red]Erro:[/red] Arquivo não encontrado: {source}")
            raise typer.Exit(code=1)
        log_source = FileSource(path)
        source_name = path.name

    if follow:
        console.print("[yellow]Modo --follow não implementado nesta versão.[/yellow]")
        raise typer.Exit(code=1)

    # Lê e parseia entradas
    entries = []
    raw_lines: list[str] = []
    with log_source:
        for line in log_source.read_lines():
            raw_lines.append(line)
            entry = parser.parse(line, source_name)
            if entry:
                entries.append(entry)

    # Analisa
    analyzer = Analyzer()
    result = analyzer.analyze(entries)

    # Diagnóstico com IA
    ai_diagnosis: str | None = None
    if ai:
        ai_cfg = cfg.get("ai", {}) or {}  # type: ignore[union-attr]
        engine = AIEngine(
            model=str(ai_cfg.get("model", "gpt-4o")),  # type: ignore[union-attr]
            endpoint=str(ai_cfg["endpoint"]) if "endpoint" in ai_cfg else None,  # type: ignore[index]
        )
        with console.status("[bold green]Consultando IA..."):
            ai_diagnosis = engine.diagnose(result, raw_lines)

    # Saída
    if output == OutputFormat.json:
        _print_json(result, ai_diagnosis)
    else:
        _print_text(result, ai_diagnosis, source_name)

    # Código de saída
    if result.error_count > 0 or result.spikes:
        raise typer.Exit(code=2)


def _get_parser(fmt: str) -> AutoParser | JsonParser | PlaintextParser | SyslogParser:
    """Retorna o parser correspondente ao formato."""
    match fmt:
        case "json":
            return JsonParser()
        case "plaintext":
            return PlaintextParser()
        case "syslog":
            return SyslogParser()
        case _:
            return AutoParser()


def _print_text(result: AnalysisResult, ai_diagnosis: str | None, source: str) -> None:
    """Exibe o resultado da análise em formato texto rico."""
    console.print(f"\n[bold]LogPulse IA[/bold] — Análise de [cyan]{source}[/cyan]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Métrica", style="dim")
    table.add_column("Valor")
    table.add_row("Total de entradas", str(result.total_entries))
    table.add_row("Erros / Críticos", f"[red]{result.error_count}[/red]")
    table.add_row("Avisos", f"[yellow]{result.warning_count}[/yellow]")
    console.print(table)

    if result.spikes:
        console.print("\n[bold red]⚡ Spikes detectados:[/bold red]")
        for spike in result.spikes:
            console.print(f"  • {spike}")

    if result.anomalies:
        console.print("\n[bold yellow]⚠️  Anomalias:[/bold yellow]")
        for anomaly in result.anomalies:
            console.print(f"  • {anomaly}")

    if ai_diagnosis:
        console.print("\n[bold green]🤖 Diagnóstico IA:[/bold green]")
        console.print(ai_diagnosis)

    console.print()


def _print_json(result: AnalysisResult, ai_diagnosis: str | None) -> None:
    """Exibe o resultado da análise em formato JSON."""
    data: dict[str, object] = {
        "total_entries": result.total_entries,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "spikes": result.spikes,
        "anomalies": result.anomalies,
    }
    if ai_diagnosis:
        data["ai_diagnosis"] = ai_diagnosis
    sys.stdout.buffer.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
    sys.stdout.write("\n")
