from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from .config import ConfigError, load_config
from .pipeline import build_providers, run_collection, sync_pending
from .providers import ProviderError
from .sheets import GoogleSheetsSink, SheetError
from .state import StateStore

app = typer.Typer(
    no_args_is_help=True,
    help="Thu thap va lam sach du lieu giao duc cong khai tu mang xa hoi.",
)
load_dotenv()
console = Console()
CONFIG_OPTION = Annotated[
    Path,
    typer.Option("--config", "-c", exists=True, dir_okay=False, readable=True),
]


def _config_or_exit(path: Path) -> dict:
    try:
        return load_config(path)
    except ConfigError as exc:
        console.print(f"[red]Cấu hình không hợp lệ:[/red] {exc}")
        raise typer.Exit(2) from exc


@app.command("init")
def init_project(
    target: Annotated[Path, typer.Option("--target", "-t")] = Path("config.yaml"),
    force: Annotated[bool, typer.Option("--force")] = False,
) -> None:
    """Tạo config.yaml từ file mẫu."""
    source = Path(__file__).resolve().parents[2] / "config.example.yaml"
    if not source.exists():
        source = Path("config.example.yaml")
    if target.exists() and not force:
        console.print(f"[yellow]{target} đã tồn tại. dùng --force nếu muốn ghi đè.[/yellow]")
        raise typer.Exit(1)
    shutil.copyfile(source, target)
    console.print(f"Đã tạo [green]{target}[/green].")


@app.command("validate")
def validate(config: CONFIG_OPTION = Path("config.yaml")) -> None:
    """Kiểm tra cấu trúc config và điều kiện quyền sử dụng."""
    loaded = _config_or_exit(config)
    enabled = [name for name in ("facebook", "threads", "reddit") if loaded[name]["enabled"]]
    console.print(f"Cấu hình hợp lệ. Provider đang bật: {', '.join(enabled) or 'không có'}")


@app.command("doctor")
def doctor(config: CONFIG_OPTION = Path("config.yaml")) -> None:
    """Kiểm tra kết nối Google Sheet và trạng thái hàng đợi."""
    loaded = _config_or_exit(config)
    table = Table("Hạng mục", "Trạng thái")
    with StateStore(Path(loaded["storage"]["state_db"])) as state:
        counts = state.counts()
    table.add_row("Pending", str(counts["pending"]))
    table.add_row("Synced", str(counts["synced"]))
    if loaded["google_sheets"].get("enabled"):
        try:
            url = GoogleSheetsSink(loaded["google_sheets"]).verify()
            table.add_row("Google Sheet", f"OK: {url}")
        except SheetError as exc:
            table.add_row("Google Sheet", f"LOI: {exc}")
    else:
        table.add_row("Google Sheet", "Tắt trong config")
    console.print(table)


@app.command("crawl")
def crawl(
    config: CONFIG_OPTION = Path("config.yaml"),
    platform: Annotated[
        list[str] | None,
        typer.Option("--platform", "-p", help="facebook, threads, reddit; lap lai de chon nhieu."),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Chỉ tạo JSONL, không ghi vào Google Sheet."),
    ] = False,
    no_sync: Annotated[
        bool,
        typer.Option("--no-sync", help="Lưu pending, chưa đẩy lên Google Sheet."),
    ] = False,
) -> None:
    """Crawl, lam sach, chong trung va mac dinh dong bo len Google Sheet."""
    loaded = _config_or_exit(config)
    selected = platform or ["facebook", "threads", "reddit"]
    invalid = sorted(set(selected) - {"facebook", "threads", "reddit"})
    if invalid:
        console.print(f"[red]Platform khong hop le:[/red] {', '.join(invalid)}")
        raise typer.Exit(2)
    try:
        providers = build_providers(loaded, selected)
        if not providers:
            console.print("[yellow]Khong co provider nao dang bat trong config.[/yellow]")
            raise typer.Exit(1)
        counts = run_collection(loaded, providers, dry_run=dry_run)
        console.print(
            f"Thu ve {counts['raw']}; chap nhan {counts['accepted']}; "
            f"loc {counts['filtered']}; trung {counts['duplicate']}."
        )
        console.print(f"JSONL: {counts['output']}")
        if not dry_run and not no_sync and loaded["google_sheets"].get("enabled"):
            result = sync_pending(loaded)
            console.print(
                f"Da day [green]{result['synced']}[/green] dong len Google Sheet; "
                f"con pending {result['remaining']}."
            )
    except (ProviderError, SheetError, ValueError) as exc:
        console.print(f"[red]Khong the hoan tat:[/red] {exc}")
        raise typer.Exit(1) from exc


@app.command("sync")
def sync(config: CONFIG_OPTION = Path("config.yaml")) -> None:
    """Thu lai viec day cac dong pending len Google Sheet."""
    loaded = _config_or_exit(config)
    try:
        result = sync_pending(loaded)
    except SheetError as exc:
        console.print(f"[red]Dong bo that bai:[/red] {exc}")
        raise typer.Exit(1) from exc
    console.print(
        f"Da dong bo [green]{result['synced']}[/green] dong; con {result['remaining']} pending."
    )


if __name__ == "__main__":
    app()
