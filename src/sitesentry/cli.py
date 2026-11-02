"""Typer CLI for SiteSentry."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from sitesentry.checks.registry import list_checks
from sitesentry.config import ScanConfig
from sitesentry.models import OutputFormat, Severity
from sitesentry.report import ReportGenerator

app = typer.Typer(
    name="sitesentry",
    help="SiteSentry – passive, safe-by-default web security scanner.",
    add_completion=False,
)

console = Console(stderr=True)
out = Console()


# ---------------------------------------------------------------------------
# scan command
# ---------------------------------------------------------------------------


@app.command()
def scan(
    url: str = typer.Argument(..., help="Target URL to scan"),
    i_have_permission: bool = typer.Option(
        False,
        "--i-have-permission",
        help="Confirm you own or are authorised to scan this target (required).",
    ),
    max_pages: int = typer.Option(50, "--max-pages", help="Maximum pages to crawl"),
    max_depth: int = typer.Option(2, "--max-depth", help="Maximum crawl depth"),
    format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json, md, html, sarif",
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Write report to FILE instead of stdout"
    ),
    fail_on: str = typer.Option(
        "high",
        "--fail-on",
        help="Exit code 2 if any finding at or above this severity (info/low/medium/high/critical)",
    ),
    allow_private: bool = typer.Option(
        False,
        "--allow-private",
        help="Allow scanning private/loopback addresses (disable SSRF guard)",
    ),
    ignore_robots: bool = typer.Option(
        False,
        "--ignore-robots",
        help="Ignore robots.txt",
    ),
) -> None:
    """Scan a URL for passive security issues."""
    if not i_have_permission:
        console.print(
            "[bold red]Error:[/bold red] You must pass [bold]--i-have-permission[/bold] "
            "to confirm you are authorised to scan this target.\n"
            "Only scan sites you own or have explicit permission to test."
        )
        raise typer.Exit(code=1)

    # Validate format
    try:
        output_format = OutputFormat(format)
    except ValueError:
        console.print(
            f"[bold red]Error:[/bold red] Invalid format {format!r}. "
            "Choose from: json, md, html, sarif"
        )
        raise typer.Exit(code=1)

    # Validate fail_on severity
    try:
        fail_severity = Severity(fail_on)
    except ValueError:
        console.print(
            f"[bold red]Error:[/bold red] Invalid --fail-on severity {fail_on!r}. "
            "Choose from: info, low, medium, high, critical"
        )
        raise typer.Exit(code=1)

    config = ScanConfig(
        target_url=url,
        confirm_permission=True,
        max_pages=max_pages,
        max_depth=max_depth,
        output_format=output_format,
        output_file=str(output) if output else None,
        fail_on=fail_severity,
        allow_private=allow_private,
        ignore_robots=ignore_robots,
    )

    console.print(f"[bold blue]SiteSentry[/bold blue] scanning [bold]{url}[/bold] …")

    # Run the scan
    from sitesentry.aggregator import ScanAggregator

    try:
        result = asyncio.run(ScanAggregator(config).run_scan())
    except Exception as exc:
        console.print(f"[bold red]Scan failed:[/bold red] {exc}")
        raise typer.Exit(code=1)

    # Render report
    gen = ReportGenerator()
    if output_format == OutputFormat.json:
        report_text = gen.to_json(result)
    elif output_format == OutputFormat.markdown:
        report_text = gen.to_markdown(result)
    elif output_format == OutputFormat.html:
        report_text = gen.to_html(result)
    elif output_format == OutputFormat.sarif:
        report_text = gen.to_sarif(result)
    else:
        report_text = gen.to_json(result)

    if output:
        output.write_text(report_text, encoding="utf-8")
        console.print(f"Report written to [bold]{output}[/bold]")
    else:
        out.print(report_text)

    # Show summary
    grade_color = {"A": "green", "B": "green", "C": "yellow", "D": "red", "F": "red"}.get(
        result.grade, "white"
    )
    console.print(
        f"\nGrade: [{grade_color}][bold]{result.grade}[/bold][/{grade_color}]  "
        f"Score: {result.score}/100  "
        f"Findings: {len(result.all_findings)}  "
        f"Pages: {result.page_count}"
    )

    # Exit code
    if result.status.value == "failed":
        raise typer.Exit(code=1)

    # Check if any finding meets or exceeds fail_on threshold
    has_failing = any(f.severity >= fail_severity for f in result.all_findings)
    if has_failing:
        console.print(
            f"[bold red]FAIL:[/bold red] Findings at or above "
            f"[bold]{fail_severity.value}[/bold] severity detected."
        )
        raise typer.Exit(code=2)

    raise typer.Exit(code=0)


# ---------------------------------------------------------------------------
# checks command
# ---------------------------------------------------------------------------


@app.command(name="checks")
def list_checks_cmd() -> None:
    """List all available security checks."""
    table = Table(title="SiteSentry Checks", show_header=True, header_style="bold blue")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title")

    for check in list_checks():
        table.add_row(check["id"], check["title"])

    out.print(table)


# ---------------------------------------------------------------------------
# serve command
# ---------------------------------------------------------------------------


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to listen on"),
) -> None:
    """Start the SiteSentry FastAPI service."""
    try:
        import uvicorn

        from sitesentry.api.app import create_app
    except ImportError as exc:
        console.print(f"[bold red]Error:[/bold red] Could not import API dependencies: {exc}")
        raise typer.Exit(code=1)

    console.print(
        f"[bold blue]SiteSentry API[/bold blue] listening on [bold]http://{host}:{port}[/bold]"
    )
    api_app = create_app()
    uvicorn.run(api_app, host=host, port=port)
