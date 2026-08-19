import time
from typing import List, Dict, Any
from fastapi.responses import JSONResponse
from nicegui import ui, app, run

from config import config
from cache_service import service, QueryResult

# Application state
chat_history: List[Dict[str, Any]] = []

# Pre-populated test scenario variations
SCENARIOS = {
    "💳 Subscriptions & Refunds": [
        ("Base Query (Miss)", "How can I cancel my subscription and get a refund?"),
        ("Variation 1 (Hit)", "I want to stop paying for my account and get my money back."),
        ("Variation 2 (Hit)", "What is the procedure to terminate membership and be reimbursed?"),
    ],
    "🔑 Password & Auth": [
        ("Base Query (Miss)", "How do I reset my account password?"),
        ("Variation 1 (Hit)", "I forgot my login password, how do I recover it?"),
        ("Variation 2 (Hit)", "Where can I change my lost credentials?"),
    ],
    "🚀 API Quotas & Limits": [
        ("Base Query (Miss)", "What are the API rate limits and quotas for CloudNova?"),
        ("Variation 1 (Hit)", "How many requests per minute can I make to the API?"),
        ("Variation 2 (Hit)", "Is there a cap on API calls per second?"),
    ],
}


# -----------------------------------------------------------------
# HEALTH CHECK ENDPOINT (/v1/health)
# -----------------------------------------------------------------
@app.get("/v1/health")
def health_check():
    """
    Health check endpoint that verifies connectivity to Valkey using a PING command
    and verifies Vertex AI authentication and permissions with 0 token consumption.
    Returns HTTP 200 with latency details if healthy, or HTTP 503 if unreachable.
    """
    valkey_ok, valkey_latency_ms, valkey_msg = service.ping_valkey()
    vertex_ok, vertex_msg = service.test_vertex_connection()

    all_healthy = valkey_ok and vertex_ok
    status_code = 200 if all_healthy else 503

    payload = {
        "status": "healthy" if all_healthy else "unhealthy",
        "valkey": {
            "connected": valkey_ok,
            "ping": valkey_msg if valkey_ok else "FAILED",
            "latency_ms": valkey_latency_ms,
            "error": None if valkey_ok else valkey_msg,
        },
        "vertex_ai": {
            "connected": vertex_ok,
            "status": vertex_msg if vertex_ok else "FAILED",
            "tokens_consumed": 0,
            "error": None if vertex_ok else vertex_msg,
        },
        "timestamp": time.time(),
    }
    return JSONResponse(status_code=status_code, content=payload)


@ui.page("/")
def index():
    # Set dark theme with modern styling
    ui.colors(primary="#1976D2", secondary="#26A69A", accent="#9C27B0", dark="#121824")
    ui.query("body").style("background-color: #0f172a; color: #f8fafc; font-family: Inter, system-ui, sans-serif;")

    # Automatically ensure Valkey index is created on startup
    service.ensure_index_created()
    valkey_connected, valkey_msg = service.test_valkey_connection()
    vertex_connected, vertex_msg = service.test_vertex_connection()

    # -------------------------------------------------------------
    # HEADER
    # -------------------------------------------------------------
    with ui.header().classes("bg-slate-900 border-b border-slate-800 px-6 py-3 items-center justify-between shadow-md"):
        with ui.row().classes("items-center gap-3"):
            ui.icon("bolt", size="32px").classes("text-amber-400")
            with ui.column().classes("gap-0"):
                ui.label("Smart Support Concierge").classes("text-xl font-bold text-white tracking-wide")
                ui.label("Valkey Semantic Cache POC with LangChain & Vertex AI").classes("text-xs text-slate-400")

        with ui.row().classes("items-center gap-3"):
            # Valkey status chip
            if valkey_connected:
                with ui.badge(color="positive").classes("px-3 py-1.5 text-xs flex items-center gap-1.5"):
                    ui.icon("check_circle", size="14px")
                    ui.label("Valkey Remote Connected")
            else:
                with ui.badge(color="negative").classes("px-3 py-1.5 text-xs flex items-center gap-1.5"):
                    ui.icon("warning", size="14px")
                    ui.label("Valkey Disconnected")

            # Vertex AI status chip
            if vertex_connected:
                with ui.badge(color="positive").classes("px-3 py-1.5 text-xs flex items-center gap-1.5"):
                    ui.icon("check_circle", size="14px")
                    ui.label(f"Vertex AI: {config.vertex_model}")
            else:
                with ui.badge(color="negative").classes("px-3 py-1.5 text-xs flex items-center gap-1.5"):
                    ui.icon("warning", size="14px")
                    ui.label(f"Vertex AI Offline ({config.vertex_model})")

    # -------------------------------------------------------------
    # PRESET TEST PROMPTS BAR
    # -------------------------------------------------------------
    with ui.card().classes("w-full bg-slate-800/80 border border-slate-700/60 p-4 mb-4 rounded-xl"):
        with ui.row().classes("items-center justify-between w-full mb-2"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("science", size="20px").classes("text-amber-400")
                ui.label("Quick Semantic Test Variations").classes("text-sm font-semibold text-slate-200")
            ui.label("Click any prompt to send and test semantic cache matching live").classes("text-xs text-slate-400")

        with ui.row().classes("w-full gap-4 flex-wrap"):
            for category, variations in SCENARIOS.items():
                with ui.column().classes("flex-1 min-w-[280px] bg-slate-900/60 p-3 rounded-lg border border-slate-700/40 gap-2"):
                    ui.label(category).classes("text-xs font-bold text-slate-300 uppercase tracking-wider")
                    for label, prompt_text in variations:
                        is_base = "Base" in label
                        btn_color = "slate-700" if is_base else "sky-900"
                        border_style = "border border-amber-500/40" if is_base else "border border-sky-500/30"
                        
                        btn = ui.button(
                            f"{label}: \"{prompt_text[:35]}...\"",
                            on_click=lambda p=prompt_text: run_prompt(p),
                        ).props("no-caps dense outline align=left").classes(f"w-full text-xs text-slate-200 {border_style} hover:bg-slate-700 transition")
                        btn.tooltip(prompt_text)

    # -------------------------------------------------------------
    # MAIN 2-COLUMN LAYOUT
    # -------------------------------------------------------------
    with ui.row().classes("w-full gap-6 items-start"):
        
        # ---------------------------------------------------------
        # LEFT: CHAT INTERFACE
        # ---------------------------------------------------------
        with ui.column().classes("flex-1 min-w-[500px] gap-4"):
            with ui.card().classes("w-full bg-slate-800/90 border border-slate-700 p-4 rounded-xl shadow-lg"):
                with ui.row().classes("items-center justify-between w-full pb-2 border-b border-slate-700"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("support_agent", size="22px").classes("text-sky-400")
                        ui.label("CloudNova Support Chat").classes("text-base font-semibold text-white")
                    ui.label("Ask customer support questions in any phrasing").classes("text-xs text-slate-400")

                # Chat message scroll area
                chat_scroll = ui.scroll_area().classes("w-full h-[460px] p-2")
                with chat_scroll:
                    chat_container = ui.column().classes("w-full gap-3")
                    with chat_container:
                        ui.chat_message(
                            text="Hello! I am your CloudNova AI Support Concierge. Ask me anything about your subscription, billing, API usage, or account settings!",
                            name="Concierge",
                            stamp="System",
                            avatar="https://robohash.org/cloudnova?set=set4",
                        ).classes("text-sm")

                # Chat input controls
                with ui.row().classes("w-full gap-2 pt-3 items-center border-t border-slate-700"):
                    query_input = ui.input(
                        placeholder="Type a support question or click a preset above...",
                    ).props("outlined dense dark autofocus").classes("flex-1 text-sm bg-slate-900 rounded-lg")
                    
                    send_btn = ui.button(
                        icon="send",
                        on_click=lambda: run_prompt(query_input.value),
                    ).props("dense color=primary").classes("px-4 py-2 rounded-lg")

                    query_input.on("keydown.enter", lambda: run_prompt(query_input.value))

        # ---------------------------------------------------------
        # RIGHT: TELEMETRY HUD & VALKEY INSPECTOR
        # ---------------------------------------------------------
        with ui.column().classes("w-[420px] gap-4"):
            
            # --- TELEMETRY METRICS HUD ---
            with ui.card().classes("w-full bg-slate-800/90 border border-slate-700 p-4 rounded-xl shadow-lg"):
                with ui.row().classes("items-center justify-between w-full pb-2 border-b border-slate-700"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("analytics", size="22px").classes("text-emerald-400")
                        ui.label("Live Telemetry HUD").classes("text-base font-semibold text-white")
                    with ui.row().classes("items-center gap-1"):
                        ui.label("Valkey HASH").classes("text-[10px] text-emerald-400 bg-emerald-950/70 px-1.5 py-0.5 rounded border border-emerald-700/50 font-mono")
                        ui.button(
                            icon="restart_alt",
                            on_click=lambda: reset_telemetry_handler(),
                        ).props("flat round dense color=slate-400 size=xs").tooltip("Reset telemetry metrics in Valkey HASH")

                # 4-Grid KPI Counters
                with ui.grid(columns=2).classes("w-full gap-3 pt-2"):
                    with ui.card().classes("bg-slate-900/80 p-3 rounded-lg border border-slate-700/60 items-center text-center"):
                        total_lbl = ui.label("0").classes("text-2xl font-bold text-white")
                        ui.label("Total Queries").classes("text-xs text-slate-400")

                    with ui.card().classes("bg-slate-900/80 p-3 rounded-lg border border-slate-700/60 items-center text-center"):
                        hit_ratio_lbl = ui.label("0%").classes("text-2xl font-bold text-emerald-400")
                        ui.label("Cache Hit Ratio").classes("text-xs text-slate-400")

                    with ui.card().classes("bg-slate-900/80 p-3 rounded-lg border border-slate-700/60 items-center text-center"):
                        time_saved_lbl = ui.label("0.0s").classes("text-2xl font-bold text-sky-400")
                        ui.label("Total Time Saved").classes("text-xs text-slate-400")

                    with ui.card().classes("bg-slate-900/80 p-3 rounded-lg border border-slate-700/60 items-center text-center"):
                        tokens_saved_lbl = ui.label("0").classes("text-2xl font-bold text-amber-400")
                        ui.label("Tokens Saved").classes("text-xs text-slate-400")

                # Last Query Speedup Banner
                last_speedup_banner = ui.card().classes("w-full bg-slate-900/90 border border-slate-700 p-3 rounded-lg mt-2 items-center justify-between")
                with last_speedup_banner:
                    with ui.row().classes("items-center justify-between w-full"):
                        last_status_lbl = ui.label("Ready for queries").classes("text-xs font-semibold text-slate-300")
                        last_latency_lbl = ui.label("-").classes("text-xs font-mono text-slate-400")

            # --- SEMANTIC TUNING CONTROLS ---
            with ui.card().classes("w-full bg-slate-800/90 border border-slate-700 p-4 rounded-xl shadow-lg"):
                with ui.row().classes("items-center justify-between w-full pb-2 border-b border-slate-700"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("tune", size="20px").classes("text-indigo-400")
                        ui.label("Semantic Distance Threshold").classes("text-sm font-semibold text-white")
                    threshold_val_lbl = ui.label(f"{config.distance_threshold:.2f}").classes("text-sm font-mono font-bold text-indigo-400")

                with ui.column().classes("w-full pt-2 gap-1"):
                    def on_threshold_change(e):
                        val = round(float(e.value), 2)
                        threshold_val_lbl.text = f"{val:.2f}"
                        service.set_threshold(val)
                        ui.notify(f"Updated semantic distance threshold to {val:.2f}", type="info", position="top-right")

                    ui.slider(
                        min=0.05,
                        max=0.50,
                        step=0.01,
                        value=config.distance_threshold,
                        on_change=on_threshold_change,
                    ).props("label label-always color=indigo dark").classes("w-full")

                    with ui.row().classes("w-full justify-between text-[11px] text-slate-400 px-1"):
                        ui.label("0.05 (Strict / Exact)")
                        ui.label("0.20 (Recommended)")
                        ui.label("0.50 (Loose / Broad)")

                with ui.row().classes("w-full justify-between items-center pt-3 border-t border-slate-700 mt-2"):
                    ui.label("Cache TTL: 3600s").classes("text-xs text-slate-400")
                    ui.button(
                        "Purge Cache",
                        icon="delete_sweep",
                        on_click=lambda: purge_cache(),
                    ).props("flat dense color=negative no-caps").classes("text-xs")

            # --- VALKEY EXPLORER & LEADERBOARD ---
            with ui.card().classes("w-full bg-slate-800/90 border border-slate-700 p-4 rounded-xl shadow-lg"):
                with ui.row().classes("items-center justify-between w-full pb-2 border-b border-slate-700"):
                    with ui.tabs().classes("text-slate-300 dense") as valkey_tabs:
                        tab_leaderboard = ui.tab("🏆 Top Prompts", icon="leaderboard").classes("text-xs font-semibold")
                        tab_explorer = ui.tab("📦 Cache Explorer", icon="storage").classes("text-xs font-semibold")

                    ui.button(
                        icon="refresh",
                        on_click=lambda: refresh_all_valkey_views(),
                    ).props("flat round dense color=primary").tooltip("Refresh Valkey data")

                with ui.tab_panels(valkey_tabs, value=tab_leaderboard).classes("w-full bg-transparent p-0 pt-2"):
                    # Panel 1: Top Prompts Leaderboard
                    with ui.tab_panel(tab_leaderboard).classes("p-0 w-full"):
                        with ui.row().classes("w-full justify-between items-center pb-1 text-slate-400 text-[11px]"):
                            ui.label("Ranked by Sorted Set hits • Prompt from HASH")
                            ui.button(
                                "Reset Scores",
                                icon="restart_alt",
                                on_click=lambda: reset_leaderboard_handler(),
                            ).props("flat dense color=amber-400 no-caps size=xs").tooltip("Reset hit counters in Valkey")

                        leaderboard_container = ui.column().classes("w-full gap-2 pt-1")

                    # Panel 2: Valkey Cache Explorer
                    with ui.tab_panel(tab_explorer).classes("p-0 w-full"):
                        with ui.row().classes("w-full justify-between items-center pb-1 text-slate-400 text-[11px]"):
                            ui.label("Raw HASH keys in Valkey")
                        cache_table_container = ui.column().classes("w-full gap-2 pt-1")

    # -------------------------------------------------------------
    # HELPER FUNCTIONS
    # -------------------------------------------------------------
    def refresh_telemetry():
        t = service.get_telemetry()
        total = t["total_queries"]
        hits = t["cache_hits"]
        ratio = (hits / total * 100.0) if total > 0 else 0.0
        total_lbl.text = str(total)
        hit_ratio_lbl.text = f"{ratio:.0f}%"
        time_saved_lbl.text = f"{(t['total_time_saved_ms'] / 1000.0):.1f}s"
        tokens_saved_lbl.text = f"{t['tokens_saved']:,}"

        if total == 0:
            last_status_lbl.text = "Ready for queries"
            last_status_lbl.classes(replace="text-xs font-semibold text-slate-300")
            last_latency_lbl.text = "-"
        elif t["last_was_hit"]:
            last_status_lbl.text = f"⚡ CACHE HIT ({t['last_speedup']:.0f}x Speedup)"
            last_status_lbl.classes(replace="text-xs font-semibold text-emerald-400")
            last_latency_lbl.text = f"{t['last_latency_ms']:.1f} ms"
        else:
            last_status_lbl.text = "🔴 CACHE MISS (Invoked Gemini)"
            last_status_lbl.classes(replace="text-xs font-semibold text-amber-400")
            last_latency_lbl.text = f"{t['last_latency_ms']:.1f} ms"

    def reset_telemetry_handler():
        service.reset_telemetry()
        ui.notify("Valkey Telemetry Metrics Reset!", type="info", position="top-right")
        refresh_telemetry()

    def refresh_leaderboard():
        leaderboard_container.clear()
        lb_items = service.get_prompt_leaderboard(limit=10)
        with leaderboard_container:
            if not lb_items:
                with ui.card().classes("w-full bg-slate-900/60 p-3 rounded-lg border border-slate-700/40 text-center"):
                    ui.label("No cache hits recorded yet.").classes("text-xs text-slate-400 font-medium")
                    ui.label("Ask questions matching cached prompts to increment Valkey sorted set hit counters!").classes("text-[11px] text-slate-500 mt-0.5")
                return

            ui.label(f"{len(lb_items)} prompt(s) on leaderboard:").classes("text-xs font-medium text-slate-300 mb-0.5")
            for item in lb_items:
                rank = item["rank"]
                rank_color = "amber-400" if rank == 1 else ("slate-300" if rank == 2 else ("amber-700" if rank == 3 else "slate-400"))
                rank_icon = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"#{rank}"))

                with ui.card().classes("w-full bg-slate-900 p-2.5 rounded-lg border border-slate-700/60 gap-1.5"):
                    with ui.row().classes("w-full items-center justify-between"):
                        with ui.row().classes("items-center gap-1.5 flex-1 min-w-0"):
                            ui.label(rank_icon).classes(f"text-xs font-bold text-{rank_color}")
                            with ui.badge(color="positive").classes("px-1.5 py-0.2 text-[10px] font-bold"):
                                ui.label(f"🔥 {item['hits']} hit{'s' if item['hits'] != 1 else ''}")
                            ui.label(item["prompt"]).classes("text-xs font-semibold text-slate-200 truncate flex-1").tooltip(item["prompt"])

                        ui.button(
                            icon="play_arrow",
                            on_click=lambda p=item["prompt"]: run_prompt(p),
                        ).props("flat round dense size=xs color=sky-400").tooltip("Send this query to test cache hit")

                    if item["response"]:
                        with ui.expansion(text="Cached Answer Preview").classes("w-full text-[11px] text-slate-400"):
                            ui.label(item["response"]).classes("text-[11px] text-slate-300 italic")

    def refresh_cache_table():
        cache_table_container.clear()
        entries = service.list_cached_entries()
        with cache_table_container:
            if not entries:
                ui.label("No items cached in Valkey yet.").classes("text-xs text-slate-400 italic py-2")
                return

            ui.label(f"{len(entries)} entry(ies) in Valkey:").classes("text-xs font-medium text-slate-300 mb-1")
            for item in entries[:5]:
                with ui.card().classes("w-full bg-slate-900 p-2.5 rounded-lg border border-slate-700/60 gap-1"):
                    with ui.row().classes("w-full items-center justify-between"):
                        with ui.row().classes("items-center gap-1.5 flex-1 min-w-0"):
                            if item.get("hits", 0) > 0:
                                with ui.badge(color="positive").classes("px-1 py-0.2 text-[9px] font-bold"):
                                    ui.label(f"{item['hits']} hits")
                            ui.label(item["prompt"]).classes("text-xs font-semibold text-slate-200 truncate flex-1 max-w-[240px]")

                        ui.button(
                            icon="close",
                            on_click=lambda k=item["key"]: delete_entry_handler(k),
                        ).props("flat round dense size=xs color=slate-400").tooltip("Delete entry")
                    ui.label(item["response"][:80] + ("..." if len(item["response"]) > 80 else "")).classes("text-[11px] text-slate-400")

    def refresh_all_valkey_views():
        refresh_telemetry()
        refresh_leaderboard()
        refresh_cache_table()

    def reset_leaderboard_handler():
        success = service.reset_leaderboard()
        if success:
            ui.notify("Valkey Leaderboard Sorted Set Reset!", type="info", position="top-right")
            refresh_all_valkey_views()
        else:
            ui.notify("Failed to reset leaderboard", type="negative", position="top-right")

    def delete_entry_handler(key: str):
        success = service.delete_entry(key)
        if success:
            ui.notify(f"Deleted cache key: {key}", type="positive", position="top-right")
            refresh_all_valkey_views()
        else:
            ui.notify("Failed to delete entry", type="negative", position="top-right")

    def purge_cache():
        service.clear_cache(clear_telemetry=True)
        ui.notify("Valkey Semantic Cache, Leaderboard & Telemetry Cleared!", type="warning", position="top-right")
        refresh_all_valkey_views()

    async def run_prompt(prompt_text: str):
        if not prompt_text or not prompt_text.strip():
            return

        clean_prompt = prompt_text.strip()
        query_input.value = ""

        # Render user message
        with chat_container:
            ui.chat_message(
                text=clean_prompt,
                name="You",
                sent=True,
                avatar="https://robohash.org/user?set=set5",
            ).classes("text-sm")
            
            # Show temporary loading spinner
            with ui.row().classes("items-center gap-2 text-slate-400 py-1") as spinner_row:
                ui.spinner("dots", size="sm", color="primary")
                ui.label("Evaluating semantic cache...").classes("text-xs")

        chat_scroll.scroll_to(percent=1.0)

        # Run query in background thread (service.query automatically persists telemetry to Valkey HASH)
        try:
            res: QueryResult = await run.io_bound(service.query, clean_prompt)
        except Exception as e:
            spinner_row.delete()
            with chat_container:
                ui.chat_message(
                    text=f"Error executing query: {str(e)}",
                    name="Error",
                    stamp="Error",
                ).classes("text-sm text-red-400")
            return

        spinner_row.delete()

        # Render Concierge Response with Telemetry Badges
        with chat_container:
            with ui.chat_message(
                text=res.answer,
                name="CloudNova Concierge",
                stamp=f"{res.latency_ms:.1f}ms",
                avatar="https://robohash.org/cloudnova?set=set4",
            ).classes("text-sm"):
                
                # Metadata Badge Area
                with ui.row().classes("w-full items-center gap-2 pt-2 flex-wrap border-t border-slate-700/40 mt-1"):
                    if res.is_cache_hit:
                        with ui.badge(color="positive").classes("px-2 py-0.5 text-[11px] font-bold"):
                            ui.label(f"⚡ CACHE HIT ({res.similarity_pct:.1f}% match)")

                        if res.hit_count:
                            with ui.badge(color="amber-900").classes("px-2 py-0.5 text-[11px] font-bold text-amber-200 border border-amber-500/50"):
                                ui.label(f"🔥 Hit #{res.hit_count}")
                        
                        ui.label(f"Distance: {res.distance:.3f}").classes("text-[11px] text-slate-400 font-mono")
                        ui.label(f"Latency: {res.latency_ms:.1f}ms").classes("text-[11px] text-emerald-400 font-mono font-bold")
                        ui.label("0 Tokens billed").classes("text-[11px] text-slate-400")

                        if res.matched_prompt:
                            with ui.expansion(text="Matched Source Query").classes("w-full text-xs text-slate-400"):
                                ui.label(f"\"{res.matched_prompt}\"").classes("italic text-slate-300")
                                if res.hit_key:
                                    ui.label(f"Valkey Key: {res.hit_key}").classes("text-[10px] font-mono text-slate-400 mt-1")
                    else:
                        with ui.badge(color="warning").classes("px-2 py-0.5 text-[11px] font-bold"):
                            ui.label("🔴 CACHE MISS")
                        
                        ui.label(f"Gemini LLM: {res.latency_ms:.0f}ms").classes("text-[11px] text-amber-400 font-mono font-bold")
                        ui.label(f"Tokens: {res.total_tokens}").classes("text-[11px] text-slate-400")
                        ui.label("Cached for subsequent queries").classes("text-[11px] text-slate-400 italic")

        chat_scroll.scroll_to(percent=1.0)
        refresh_all_valkey_views()

    # Initial view population (loads persisted telemetry from Valkey HASH)
    refresh_all_valkey_views()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="Smart Support Concierge — Valkey Semantic Cache",
        port=8080,
        dark=True,
        reload=False,
    )
