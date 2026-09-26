# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "rich",
# ]
# ///
"""
Live Crypto Funding Rate & Delta-Neutral Arbitrage Scanner.
Scans Hyperliquid (L1 DEX Perp) and Binance (CEX Perp) public APIs to detect:
1. Highest Cash & Carry yields (Long Spot + Short Perp).
2. Cross-exchange funding spreads (Long Perp Exchange A + Short Perp Exchange B).
"""

import os
import sys
import argparse
from datetime import datetime
import httpx

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich import box

console = Console()

HYPERLIQUID_API = "https://api.hyperliquid.xyz/info"
BINANCE_PREMIUM_API = "https://fapi.binance.com/fapi/v1/premiumIndex"


def fetch_hyperliquid_data(client: httpx.Client) -> dict[str, dict]:
    """Fetch Hyperliquid perps metadata and context."""
    res = client.post(
        HYPERLIQUID_API,
        json={"type": "metaAndAssetCtxs"},
        headers={"Content-Type": "application/json"},
        timeout=10.0,
    )
    res.raise_for_status()
    data = res.json()
    universe = data[0]["universe"]
    ctxs = data[1]

    hl_markets = {}
    for meta, ctx in zip(universe, ctxs):
        name = meta.get("name")
        if not name or meta.get("isDelisted", False):
            continue

        try:
            funding_1h = float(ctx.get("funding", 0.0))
            mark_px = float(ctx.get("markPx", 0.0))
            oi_coins = float(ctx.get("openInterest", 0.0))
            volume_24h = float(ctx.get("dayNtlVlm", 0.0))
            oi_usd = oi_coins * mark_px
            apr = funding_1h * 24 * 365 * 100.0  # Annualized %

            hl_markets[name] = {
                "symbol": name,
                "price": mark_px,
                "funding_rate": funding_1h,
                "apr": apr,
                "oi_usd": oi_usd,
                "volume_24h": volume_24h,
            }
        except (ValueError, TypeError):
            continue

    return hl_markets


def fetch_binance_data(client: httpx.Client) -> dict[str, dict]:
    """Fetch Binance USDT perps funding rate data."""
    res = client.get(
        BINANCE_PREMIUM_API,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=10.0,
    )
    res.raise_for_status()
    items = res.json()

    bn_markets = {}
    for item in items:
        symbol = item.get("symbol", "")
        if not symbol.endswith("USDT"):
            continue

        raw_asset = symbol[:-4]
        # Normalize common 1000x prefixes (e.g. 1000PEPE -> PEPE, kPEPE)
        base_asset = raw_asset.removeprefix("1000").removeprefix("1M")

        try:
            funding_8h = float(item.get("lastFundingRate", 0.0))
            mark_px = float(item.get("markPrice", 0.0))
            apr = funding_8h * 3 * 365 * 100.0  # Annualized % (3 intervals/day)

            bn_markets[base_asset] = {
                "symbol": base_asset,
                "raw_symbol": symbol,
                "price": mark_px,
                "funding_rate": funding_8h,
                "apr": apr,
            }
        except (ValueError, TypeError):
            continue

    return bn_markets

def format_rate(apr: float) -> str:
    color = "green" if apr > 0 else "red"
    return f"[{color}]{apr:+.2f}%[/{color}]"


def send_telegram_alert(top_hl: list[dict], top_arb: list[dict]) -> bool:

    """Send HTML briefing of top funding and arb opportunities to Telegram."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_AT")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "387794487")

    if not token:
        console.print("[yellow]⚠️ Cannot send Telegram alert: TELEGRAM_BOT_TOKEN / TELEGRAM_BOT_AT not found.[/yellow]")
        return False

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M WIB")
    lines = [
        f"⚡ <b>Crypto Funding & Basis Alert</b> ({now_str})",
        "",
        "🌟 <b>Top Cash & Carry (Hyperliquid)</b>",
    ]

    for m in top_hl[:5]:
        lines.append(
            f"• <b>{m['symbol']}</b>: <code>{m['apr']:+.1f}% APR</code> (${m['oi_usd']/1e6:.1f}M OI)"
        )

    lines.append("")
    lines.append("🔄 <b>Top Cross-Perp Spreads</b>")
    for pair in top_arb[:5]:
        lines.append(
            f"• <b>{pair['asset']}</b>: <code>+{pair['spread_abs']:.1f}% Spread</code> ({pair['strategy']})"
        )

    lines.append("")
    lines.append("<i>Zero-directional delta-neutral opportunity scanner</i>")
    message = "\n".join(lines)

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        with httpx.Client() as client:
            resp = client.post(url, json=payload, timeout=10.0)
            if resp.is_success:
                console.print(f"[bold green]✅ Telegram alert sent successfully to chat {chat_id}[/bold green]")
                return True
            else:
                console.print(f"[red]❌ Telegram API error: {resp.text}[/red]")
                return False
    except Exception as e:
        console.print(f"[red]❌ Failed to send Telegram alert: {e}[/red]")
        return False


def run_scanner():
    parser = argparse.ArgumentParser(description="Crypto Funding Rate & Arbitrage Scanner")
    parser.add_argument("-n", "--notify", action="store_true", help="Send alert to Telegram")
    parser.add_argument("--min-spread", type=float, default=25.0, help="Minimum spread APR for alert filter")
    parser.add_argument("--min-apr", type=float, default=20.0, help="Minimum HL APR for alert filter")
    args = parser.parse_args()

    console.print(
        Panel.fit(
            "[bold cyan]⚡ Crypto Delta-Neutral Funding & Basis Scanner[/bold cyan]\n"
            f"[dim]Data Sources: Hyperliquid L1 (1h settlement) | Binance USDT-M (8h settlement) — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
            box=box.ROUNDED,
        )
    )

    with console.status("[bold yellow]Fetching live market data...[/bold yellow]"):
        with httpx.Client() as client:
            hl_data = fetch_hyperliquid_data(client)
            bn_data = fetch_binance_data(client)

    # Filter for minimum liquidity to avoid illiquid traps ($200k+ OI or $300k+ volume on HL)
    liquid_hl = [
        m for m in hl_data.values()
        if m["oi_usd"] >= 200_000 and m["volume_24h"] >= 300_000
    ]
    sorted_hl = sorted(liquid_hl, key=lambda x: x["apr"], reverse=True)

    # 1. Hyperliquid Top Opportunities
    hl_table = Table(
        title="🌟 Hyperliquid Top Funding Yields (Cash & Carry: Long Spot + Short Perp)",
        box=box.SIMPLE_HEAVY,
        header_style="bold magenta",
    )
    hl_table.add_column("Asset", style="cyan", no_wrap=True)
    hl_table.add_column("Price (USD)", justify="right")
    hl_table.add_column("1h Rate", justify="right")
    hl_table.add_column("Annualized APR", justify="right")
    hl_table.add_column("Open Interest", justify="right")
    hl_table.add_column("24h Volume", justify="right")

    for m in sorted_hl[:8]:
        hl_table.add_row(
            m["symbol"],
            f"${m['price']:,.4f}" if m['price'] < 1 else f"${m['price']:,.2f}",
            f"{m['funding_rate'] * 100:+.4f}%",
            format_rate(m["apr"]),
            f"${m['oi_usd'] / 1_000_000:.2f}M",
            f"${m['volume_24h'] / 1_000_000:.2f}M",
        )

    console.print(hl_table)
    console.print()

    # 2. Cross-Exchange Arbitrage (No Spot Needed! Long Perp on A + Short Perp on B)
    arb_pairs = []
    for asset, hl_item in hl_data.items():
        if asset in bn_data and hl_item["oi_usd"] >= 200_000:
            bn_item = bn_data[asset]
            spread = bn_item["apr"] - hl_item["apr"]
            arb_pairs.append({
                "asset": asset,
                "hl_apr": hl_item["apr"],
                "bn_apr": bn_item["apr"],
                "spread_abs": abs(spread),
                "strategy": "Short Binance / Long HL" if spread > 0 else "Short HL / Long Binance",
                "oi_usd": hl_item["oi_usd"],
            })

    sorted_arb = sorted(arb_pairs, key=lambda x: x["spread_abs"], reverse=True)

    arb_table = Table(
        title="⚡ Cross-Exchange Perp Spread (Pure Delta-Neutral: Long Perp A + Short Perp B)",
        box=box.SIMPLE_HEAVY,
        header_style="bold green",
    )
    arb_table.add_column("Asset", style="cyan", no_wrap=True)
    arb_table.add_column("Hyperliquid APR", justify="right")
    arb_table.add_column("Binance APR", justify="right")
    arb_table.add_column("Spread (Net APR)", justify="right")
    arb_table.add_column("Recommended Trade", style="yellow")
    arb_table.add_column("HL Open Interest", justify="right")

    for pair in sorted_arb[:8]:
        arb_table.add_row(
            pair["asset"],
            format_rate(pair["hl_apr"]),
            format_rate(pair["bn_apr"]),
            f"[bold underline green]{pair['spread_abs']:.2f}%[/bold underline green]",
            pair["strategy"],
            f"${pair['oi_usd'] / 1_000_000:.2f}M",
        )

    console.print(arb_table)
    console.print()

    # Insight Panel
    avg_hl_apr = sum(m["apr"] for m in liquid_hl) / len(liquid_hl) if liquid_hl else 0.0
    sentiment = "Bullish (Longs paying Shorts)" if avg_hl_apr > 5 else "Neutral/Bearish"
    
    console.print(
        Panel(
            f"• [bold]Market Regime:[/bold] {sentiment} (Avg HL APR: {avg_hl_apr:+.2f}%)\n"
            f"• [bold]Cash & Carry Edge:[/bold] Top candidate yields [green]{sorted_hl[0]['apr']:.2f}% APR[/green] ({sorted_hl[0]['symbol']}).\n"
            f"• [bold]Cross-Perp Edge:[/bold] Highest spread is [green]{sorted_arb[0]['spread_abs']:.2f}%[/green] on {sorted_arb[0]['asset']} ({sorted_arb[0]['strategy']}).\n"
            f"• [bold]Execution Fee Notice:[/bold] Hyperliquid taker fee is ~0.035% (maker 0.01%), Binance VIP0 is ~0.05%. Roundtrip cost ~0.08% is repaid in ~1-2 days of funding.",
            title="💡 Quant Takeaways",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )

    if args.notify:
        send_telegram_alert(sorted_hl, sorted_arb)


if __name__ == "__main__":
    run_scanner()

