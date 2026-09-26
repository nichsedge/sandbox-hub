# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "rich",
# ]
# ///
"""
Delta-Neutral Paper Trading & Yield Simulator.
Simulates real delta-neutral positions (Cash & Carry or Cross-Perp) using live market prices.
Tracks trading fees, price drift, and accrued funding yield in a local SQLite database.
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

DB_DIR = Path(__file__).parent / "data"
DB_PATH = DB_DIR / "paper_trades.db"
HYPERLIQUID_API = "https://api.hyperliquid.xyz/info"
BINANCE_PREMIUM_API = "https://fapi.binance.com/fapi/v1/premiumIndex"


def init_db():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                strategy TEXT NOT NULL, -- 'cash_and_carry' or 'cross_perp'
                notional_usd REAL NOT NULL,
                entry_time TEXT NOT NULL,
                entry_px_hl REAL NOT NULL,
                entry_px_bn REAL NOT NULL,
                entry_funding_hl REAL NOT NULL,
                entry_funding_bn REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'OPEN', -- 'OPEN' or 'CLOSED'
                close_time TEXT,
                close_px_hl REAL,
                close_px_bn REAL,
                total_fees_usd REAL NOT NULL,
                realized_pnl_usd REAL DEFAULT 0.0
            )
        """)
        conn.commit()


def get_current_market_data(symbol: str) -> tuple[float, float, float, float]:
    """Fetch current price and funding rate for symbol on Hyperliquid and Binance."""
    norm_symbol = symbol.upper()
    with httpx.Client(timeout=10.0) as client:
        # 1. Hyperliquid
        hl_res = client.post(HYPERLIQUID_API, json={"type": "metaAndAssetCtxs"})
        hl_data = hl_res.json()
        hl_universe = hl_data[0]["universe"]
        hl_ctxs = hl_data[1]

        hl_px = 0.0
        hl_funding_1h = 0.0
        for meta, ctx in zip(hl_universe, hl_ctxs):
            if meta.get("name") == norm_symbol:
                hl_px = float(ctx.get("markPx", 0.0))
                hl_funding_1h = float(ctx.get("funding", 0.0))
                break

        # 2. Binance
        bn_res = client.get(BINANCE_PREMIUM_API, headers={"User-Agent": "Mozilla/5.0"})
        bn_items = bn_res.json()
        bn_px = 0.0
        bn_funding_8h = 0.0
        target_pair = f"{norm_symbol}USDT"
        target_1000_pair = f"1000{norm_symbol}USDT"

        for item in bn_items:
            s = item.get("symbol", "")
            if s == target_pair or s == target_1000_pair:
                bn_px = float(item.get("markPrice", 0.0))
                bn_funding_8h = float(item.get("lastFundingRate", 0.0))
                break

    return hl_px, hl_funding_1h, bn_px, bn_funding_8h


def open_position(symbol: str, strategy: str, size_usd: float):
    init_db()
    norm_symbol = symbol.upper()
    with console.status(f"[bold yellow]Fetching live market data for {norm_symbol}...[/bold yellow]"):
        hl_px, hl_funding_1h, bn_px, bn_funding_8h = get_current_market_data(norm_symbol)

    if hl_px == 0.0:
        console.print(f"[bold red]❌ Error:[/bold red] Could not find symbol '{norm_symbol}' on Hyperliquid.")
        return

    if strategy == "cross_perp" and bn_px == 0.0:
        console.print(f"[bold red]❌ Error:[/bold red] Could not find symbol '{norm_symbol}' on Binance for cross-perp.")
        return

    # Approximate fees:
    # Hyperliquid taker 0.035%, Binance taker 0.05%
    if strategy == "cash_and_carry":
        # Spot buy (0.05%) + HL Short Perp (0.035%)
        open_fee = size_usd * 0.00085
    else:
        # HL Perp (0.035%) + Binance Perp (0.05%)
        open_fee = size_usd * 0.00085

    now_iso = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO positions (
                symbol, strategy, notional_usd, entry_time,
                entry_px_hl, entry_px_bn, entry_funding_hl, entry_funding_bn,
                status, total_fees_usd
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
        """, (
            norm_symbol, strategy, size_usd, now_iso,
            hl_px, bn_px, hl_funding_1h, bn_funding_8h, open_fee
        ))
        pos_id = cursor.lastrowid
        conn.commit()

    hl_apr = hl_funding_1h * 24 * 365 * 100
    bn_apr = bn_funding_8h * 3 * 365 * 100

    console.print(
        Panel(
            f"✅ [bold green]Paper Position Opened #{pos_id}[/bold green]\n\n"
            f"• [bold]Asset:[/bold] {norm_symbol}\n"
            f"• [bold]Strategy:[/bold] {strategy}\n"
            f"• [bold]Notional Size:[/bold] ${size_usd:,.2f} USD (Delta-Neutral)\n"
            f"• [bold]Entry Price HL:[/bold] ${hl_px:,.4f} | [bold]Binance:[/bold] ${bn_px:,.4f}\n"
            f"• [bold]Entry Funding APR:[/bold] HL: {hl_apr:+.2f}% | Binance: {bn_apr:+.2f}%\n"
            f"• [bold]Initial Opening Fee:[/bold] ${open_fee:,.4f} USD\n\n"
            f"[dim]Tracking started. Run `uv run tools/crypto-quant/paper_trader.py status` to inspect accrued yield.[/dim]",
            title="🎯 Position Confirmation",
            border_style="green",
            box=box.ROUNDED,
        )
    )


def show_status():
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM positions WHERE status = 'OPEN'").fetchall()

    if not rows:
        console.print("[yellow]No open paper positions found. Open one with `open <symbol>`.[/yellow]")
        return

    table = Table(
        title="📈 Active Delta-Neutral Paper Positions",
        box=box.SIMPLE_HEAVY,
        header_style="bold cyan",
    )
    table.add_column("ID", justify="center")
    table.add_column("Asset", style="cyan bold")
    table.add_column("Strategy")
    table.add_column("Size (USD)", justify="right")
    table.add_column("Age", justify="center")
    table.add_column("Funding Yield", justify="right")
    table.add_column("Fees", justify="right")
    table.add_column("Net PnL", justify="right")
    table.add_column("Net ROI", justify="right")

    now = datetime.now(timezone.utc)

    for row in rows:
        entry_time = datetime.fromisoformat(row["entry_time"])
        elapsed_seconds = (now - entry_time).total_seconds()
        elapsed_hours = elapsed_seconds / 3600.0

        hl_px, cur_hl_funding, bn_px, cur_bn_funding = get_current_market_data(row["symbol"])
        
        # Calculate accrued funding:
        # Use average of entry and current funding rate
        avg_hl_funding = (row["entry_funding_hl"] + cur_hl_funding) / 2.0
        accrued_funding_hl = row["notional_usd"] * (avg_hl_funding * elapsed_hours)

        if row["strategy"] == "cross_perp":
            # For cross-perp: Short HL, Long Binance
            avg_bn_funding_8h = (row["entry_funding_bn"] + cur_bn_funding) / 2.0
            avg_bn_funding_1h = avg_bn_funding_8h / 8.0
            accrued_funding_bn = row["notional_usd"] * (avg_bn_funding_1h * elapsed_hours)
            # Net funding received
            total_accrued_funding = accrued_funding_hl - accrued_funding_bn
        else:
            # Cash and carry: Short Perp receives funding
            total_accrued_funding = accrued_funding_hl

        fees = row["total_fees_usd"]
        net_pnl = total_accrued_funding - fees
        net_roi = (net_pnl / row["notional_usd"]) * 100.0

        pnl_color = "green" if net_pnl >= 0 else "red"
        age_str = f"{elapsed_hours:.1f}h" if elapsed_hours >= 1 else f"{elapsed_seconds/60:.0f}m"

        table.add_row(
            str(row["id"]),
            row["symbol"],
            row["strategy"],
            f"${row['notional_usd']:,.2f}",
            age_str,
            f"[green]+${total_accrued_funding:,.4f}[/green]",
            f"[red]-${fees:,.4f}[/red]",
            f"[{pnl_color}]{net_pnl:+,.4f}[/{pnl_color}]",
            f"[{pnl_color}]{net_roi:+.2f}%[/{pnl_color}]",
        )

    console.print(table)


def close_position(pos_id: int):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM positions WHERE id = ? AND status = 'OPEN'", (pos_id,)).fetchone()

        if not row:
            console.print(f"[bold red]❌ Error:[/bold red] Open position #{pos_id} not found.")
            return

        now = datetime.now(timezone.utc)
        entry_time = datetime.fromisoformat(row["entry_time"])
        elapsed_hours = (now - entry_time).total_seconds() / 3600.0

        hl_px, cur_hl_funding, bn_px, cur_bn_funding = get_current_market_data(row["symbol"])
        avg_hl_funding = (row["entry_funding_hl"] + cur_hl_funding) / 2.0
        accrued_funding = row["notional_usd"] * (avg_hl_funding * elapsed_hours)

        close_fee = row["notional_usd"] * 0.00085
        total_fees = row["total_fees_usd"] + close_fee
        realized_pnl = accrued_funding - total_fees

        conn.execute("""
            UPDATE positions SET
                status = 'CLOSED',
                close_time = ?,
                close_px_hl = ?,
                close_px_bn = ?,
                total_fees_usd = ?,
                realized_pnl_usd = ?
            WHERE id = ?
        """, (now.isoformat(), hl_px, bn_px, total_fees, realized_pnl, pos_id))
        conn.commit()

    console.print(
        Panel(
            f"🏁 [bold]Position #{pos_id} Closed[/bold]\n\n"
            f"• Asset: {row['symbol']}\n"
            f"• Realized Funding: [green]+${accrued_funding:,.4f}[/green]\n"
            f"• Total Roundtrip Fees: [red]-${total_fees:,.4f}[/red]\n"
            f"• Net Realized PnL: [{'green' if realized_pnl >= 0 else 'red'}]{realized_pnl:+,.4f} USD[/{'green' if realized_pnl >= 0 else 'red'}]",
            border_style="yellow",
            box=box.ROUNDED,
        )
    )


def main():
    parser = argparse.ArgumentParser(description="Delta-Neutral Paper Trading Simulator")
    subparsers = parser.add_subparsers(dest="command")

    # Open command
    open_parser = subparsers.add_parser("open", help="Open a new paper position")
    open_parser.add_argument("symbol", help="Asset symbol (e.g. SKY, ETHFI, MNT)")
    open_parser.add_argument("--strategy", choices=["cash_and_carry", "cross_perp"], default="cash_and_carry")
    open_parser.add_argument("--size", type=float, default=1000.0, help="Notional position size in USD (default: 1000)")

    # Status command
    subparsers.add_parser("status", help="Show active paper positions and accrued yield")

    # Close command
    close_parser = subparsers.add_parser("close", help="Close a position")
    close_parser.add_argument("id", type=int, help="Position ID to close")

    args = parser.parse_args()

    if args.command == "open":
        open_position(args.symbol, args.strategy, args.size)
    elif args.command == "status":
        show_status()
    elif args.command == "close":
        close_position(args.id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
