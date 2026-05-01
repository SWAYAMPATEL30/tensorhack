#!/usr/bin/env python3
"""
start_monitor.py — Live terminal + browser monitoring dashboard
Usage: python scripts/start_monitor.py
"""
import sys, os, time, json, datetime, threading, webbrowser, subprocess, requests
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich import box
    RICH = True
except ImportError:
    RICH = False
    print("[!] 'rich' not installed. Install: pip install rich")
    print("   Running in simple mode...")

ROOT   = Path(__file__).resolve().parent.parent
API    = "http://localhost:8000"
LOG_DIR= ROOT / "logs"; LOG_DIR.mkdir(exist_ok=True)
today  = datetime.date.today().strftime("%Y%m%d")
LOG_FILE = LOG_DIR / f"monitor_{today}.jsonl"

console = Console() if RICH else None

def get(path):
    try: return requests.get(f"{API}{path}", timeout=5).json()
    except: return {}

def post(path, body={}):
    try: return requests.post(f"{API}{path}", json=body, timeout=5).json()
    except: return {}

def get_health():
    return get("/api/health/detailed")

def get_summary():
    return get("/api/analytics/summary")

def alert_color(level):
    return {"RED":"red","YELLOW":"yellow","GREEN":"green"}.get(level,"white")

def uptime_str(s):
    h = s // 3600; m = (s % 3600) // 60; sec = s % 60
    return f"{h}h {m}m {sec}s"

# ── Save monitor snapshot to JSONL ────────────────────────────────────
def save_snapshot(health, summary):
    snap = {"ts": datetime.datetime.utcnow().isoformat(), "health": health, "summary": summary}
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(snap) + "\n")

# ── Simple mode (no rich) ────────────────────────────────────────────
def simple_monitor():
    while True:
        h = get_health()
        s = get_summary()
        save_snapshot(h, s)
        os.system('cls' if os.name=='nt' else 'clear')
        now = datetime.datetime.now().strftime("%H:%M:%S")
        uptime = uptime_str(h.get("uptime_seconds", 0))
        print(f"\n LOAN WIZARD MONITOR — {now}  Uptime: {uptime}")
        print("="*65)
        print(f" Sessions: {s.get('total_sessions',0)} | Approved: {s.get('approved',0)} | Rejected: {s.get('rejected',0)} | Fraud: {s.get('fraud_detected',0)}")
        print("-"*65)
        print(" MODEL STATUS:")
        for nm, ms in h.get("models",{}).items():
            status = "OK" if ms.get("loaded") else "FAIL"
            lat = ms.get("latency_ms",0)
            warn = " [SLOW]" if lat > 500 else ""
            print(f"   {'[OK]' if status=='OK' else '[!!]'} {nm:<28} {lat:.0f}ms {warn}")
        print("-"*65)
        sys_info = h.get("system",{})
        print(f" CPU: {sys_info.get('cpu_percent',0):.1f}%  RAM: {sys_info.get('ram_used_mb',0):.0f}MB  Disk: {sys_info.get('disk_free_gb',0):.1f}GB free")
        alerts = h.get("alerts",[])
        if alerts:
            print("\n ALERTS:")
            for a in alerts: print(f"   [{a['level']}] {a['message']}")
        print("\n Recent sessions:")
        for s2 in s.get("recent_sessions",[])[:5]:
            print(f"   {s2.get('created_at','')[:16]}  {(s2.get('applicant_name') or 'Unknown'):<25}  {s2.get('decision','—')}")
        print(f"\n Log: {LOG_FILE}")
        time.sleep(2)

# ── Rich mode ────────────────────────────────────────────────────────
def rich_monitor():
    with Live(refresh_per_second=0.5, screen=True) as live:
        while True:
            h = get_health(); s = get_summary()
            save_snapshot(h, s)
            now = datetime.datetime.now().strftime("%H:%M:%S")
            uptime = uptime_str(h.get("uptime_seconds",0))
            sys_info = h.get("system",{})
            alerts = h.get("alerts",[])

            # Header
            status_text = "[bold green]ALL SYSTEMS GO[/]" if not any(a["level"]=="RED" for a in alerts) else "[bold red]ALERTS ACTIVE[/]"
            header = f"[bold]Time: {now}[/]  |  [bold]Uptime: {uptime}[/]  |  Status: {status_text}"
            header_panel = Panel(header, title="[bold blue]POONAWALLA FINCORP — LOAN WIZARD LIVE MONITOR[/]", border_style="blue")

            # Model Status Table
            model_table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan", expand=True)
            model_table.add_column("Model", style="bold")
            model_table.add_column("Status", justify="center")
            model_table.add_column("Latency", justify="right")
            model_table.add_column("Today", justify="right")
            model_table.add_column("Drift", justify="center")

            DRIFT = {"credit_risk":"2.1%","fraud":"1.3%","age_validator":"0.4%","offer_engine":"3.2%","intent":"5.8%","emotion":"0.8%","whisper":"—","yolo":"—"}
            for nm, ms in h.get("models",{}).items():
                lat = ms.get("latency_ms",0)
                loaded = ms.get("loaded", False)
                status_str = "[green]LOADED[/]" if loaded else "[red]FAILED[/]"
                lat_str = f"[red]{lat:.0f}ms[/]" if lat>2000 else (f"[yellow]{lat:.0f}ms[/]" if lat>500 else f"[green]{lat:.0f}ms[/]")
                drift_str = DRIFT.get(nm,"—")
                model_table.add_row(nm, status_str, lat_str, str(ms.get("predictions_today",0)), drift_str)

            model_panel = Panel(model_table, title="[bold]Model Status[/]", border_style="cyan")

            # Today Stats Panel
            stats_text = (
                f"Sessions: [bold]{s.get('total_sessions',0)}[/]  |  "
                f"[green]Approved: {s.get('approved',0)}[/]  |  "
                f"[red]Rejected: {s.get('rejected',0)}[/]  |  "
                f"[orange3]Fraud: {s.get('fraud_detected',0)}[/]  |  "
                f"Avg Loan: [bold]Rs.{s.get('avg_loan_amount',0):,}[/]  |  "
                f"CPU: {sys_info.get('cpu_percent',0):.1f}%  RAM: {sys_info.get('ram_used_mb',0):.0f}MB"
            )
            stats_panel = Panel(stats_text, title="[bold]Today's Stats[/]", border_style="green")

            # Live Feed
            feed_table = Table(box=box.SIMPLE, expand=True, show_header=True, header_style="bold")
            feed_table.add_column("Time")
            feed_table.add_column("Applicant", style="bold")
            feed_table.add_column("Decision", justify="center")
            feed_table.add_column("Risk", justify="center")
            feed_table.add_column("Offer")

            for sess in s.get("recent_sessions",[])[:8]:
                dec = sess.get("decision","—")
                dec_color = "green" if dec=="APPROVED" else ("red" if dec=="REJECTED" else "yellow")
                r = sess.get("risk_band","—")
                r_color = "green" if r=="LOW" else ("red" if r=="HIGH" else "yellow")
                offer = f"Rs.{sess.get('offer_amount',0):,}" if sess.get('offer_amount') else "—"
                feed_table.add_row(
                    (sess.get("created_at") or "")[:16],
                    (sess.get("applicant_name") or "Unknown")[:25],
                    f"[{dec_color}]{dec}[/]",
                    f"[{r_color}]{r}[/]",
                    offer
                )
            feed_panel = Panel(feed_table, title="[bold]Live Session Feed[/]", border_style="magenta")

            # Alerts
            if alerts:
                alert_lines = "\n".join(f"[{alert_color(a['level'])}][{a['level']}] {a['message']}[/]" for a in alerts)
            else:
                alert_lines = "[green]No active alerts[/]"
            alert_panel = Panel(alert_lines, title="[bold]Alerts[/]", border_style="red" if any(a["level"]=="RED" for a in alerts) else "green")

            # Compose layout
            from rich.columns import Columns
            layout = Layout()
            layout.split_column(
                Layout(header_panel, size=3),
                Layout(stats_panel, size=4),
                Layout(Columns([model_panel, alert_panel])),
                Layout(feed_panel),
            )
            live.update(layout)
            time.sleep(2)

# ── Main ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\nPoonawalla Fincorp — Live Monitor")
    print(f"API: {API}")
    print(f"Log: {LOG_FILE}")

    # Open browser monitor
    monitor_html = ROOT / "frontend" / "admin" / "monitor.html"
    if monitor_html.exists():
        print(f"Opening browser monitor: {monitor_html}")
        webbrowser.open(f"file:///{monitor_html}")
        time.sleep(1)

    print("Starting terminal monitor (Ctrl+C to exit)...\n")
    try:
        if RICH:
            rich_monitor()
        else:
            simple_monitor()
    except KeyboardInterrupt:
        print("\nMonitor stopped.")
