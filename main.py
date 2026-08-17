import asyncio
from typing import List, Dict, Any
from nicegui import ui, app, run

from config import config
from cache_service import service, QueryResult

# Application state
chat_history: List[Dict[str, Any]] = []
metrics = {
    "total_queries": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "tokens_saved": 0,
    "total_time_saved_ms": 0.0,
    "last_latency_ms": 0.0,
    "last_was_hit": False,
    "last_speedup": 1.0,
}

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
                with ui.badge(color="primary").classes("px-3 py-1.5 text-xs flex items-center gap-1.5"):
                    ui.icon("psychology", size="14px")
                    ui.label(f"Vertex AI: {config.vertex_model}")
            else:
                with ui.badge(color="warning").classes("px-3 py-1.5 text-xs flex items-center gap-1.5"):
                    ui.icon("error", size="14px")
                    ui.label("Vertex AI Offline")

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
                    ui.label("Real-time performance").classes("text-xs text-slate-400")

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

            # --- VALKEY CACHE EXPLORER ---
            with ui.card().classes("w-full bg-slate-800/90 border border-slate-700 p-4 rounded-xl shadow-lg"):
                with ui.row().classes("items-center justify-between w-full pb-2 border-b border-slate-700"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("storage", size="20px").classes("text-cyan-400")
                        ui.label("Valkey Cache Explorer").classes("text-sm font-semibold text-white")
                    
                    ui.button(
                        icon="refresh",
                        on_click=lambda: refresh_cache_table(),
                    ).props("flat dense color=primary").tooltip("Refresh cached entries from Valkey")

                cache_table_container = ui.column().classes("w-full pt-2")

    # -------------------------------------------------------------
    # HELPER FUNCTIONS
    # -------------------------------------------------------------
    def refresh_telemetry():
        total = metrics["total_queries"]
        hits = metrics["cache_hits"]
        ratio = (hits / total * 100.0) if total > 0 else 0.0
        total_lbl.text = str(total)
        hit_ratio_lbl.text = f"{ratio:.0f}%"
        time_saved_lbl.text = f"{(metrics['total_time_saved_ms'] / 1000.0):.1f}s"
        tokens_saved_lbl.text = f"{metrics['tokens_saved']:,}"

        if metrics["last_was_hit"]:
            last_status_lbl.text = f"⚡ CACHE HIT ({metrics['last_speedup']:.0f}x Speedup)"
            last_status_lbl.classes(replace="text-xs font-semibold text-emerald-400")
        else:
            last_status_lbl.text = "🔴 CACHE MISS (Invoked Gemini)"
            last_status_lbl.classes(replace="text-xs font-semibold text-amber-400")
        last_latency_lbl.text = f"{metrics['last_latency_ms']:.1f} ms"

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
                        ui.label(item["prompt"]).classes("text-xs font-semibold text-slate-200 truncate max-w-[280px]")
                        ui.button(
                            icon="close",
                            on_click=lambda k=item["key"]: delete_entry_handler(k),
                        ).props("flat round dense size=xs color=slate-400").tooltip("Delete entry")
                    ui.label(item["response"][:80] + ("..." if len(item["response"]) > 80 else "")).classes("text-[11px] text-slate-400")

    def delete_entry_handler(key: str):
        success = service.delete_entry(key)
        if success:
            ui.notify(f"Deleted cache key: {key}", type="positive", position="top-right")
            refresh_cache_table()
        else:
            ui.notify("Failed to delete entry", type="negative", position="top-right")

    def purge_cache():
        service.clear_cache()
        ui.notify("Valkey Semantic Cache Cleared!", type="warning", position="top-right")
        refresh_cache_table()

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

        # Run query in background thread
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

        # Update global telemetry metrics
        metrics["total_queries"] += 1
        metrics["last_latency_ms"] = res.latency_ms
        metrics["last_was_hit"] = res.is_cache_hit

        if res.is_cache_hit:
            metrics["cache_hits"] += 1
            # Assuming baseline LLM latency is ~1200ms
            saved_ms = max(0.0, 1200.0 - res.latency_ms)
            metrics["total_time_saved_ms"] += saved_ms
            metrics["tokens_saved"] += 250  # Average saved tokens
            speedup = 1200.0 / max(res.latency_ms, 1.0)
            metrics["last_speedup"] = speedup
        else:
            metrics["cache_misses"] += 1
            metrics["last_speedup"] = 1.0

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
                        
                        ui.label(f"Distance: {res.distance:.3f}").classes("text-[11px] text-slate-400 font-mono")
                        ui.label(f"Latency: {res.latency_ms:.1f}ms").classes("text-[11px] text-emerald-400 font-mono font-bold")
                        ui.label("0 Tokens billed").classes("text-[11px] text-slate-400")

                        if res.matched_prompt:
                            with ui.expansion(text="Matched Source Query").classes("w-full text-xs text-slate-400"):
                                ui.label(f"\"{res.matched_prompt}\"").classes("italic text-slate-300")
                    else:
                        with ui.badge(color="warning").classes("px-2 py-0.5 text-[11px] font-bold"):
                            ui.label("🔴 CACHE MISS")
                        
                        ui.label(f"Gemini LLM: {res.latency_ms:.0f}ms").classes("text-[11px] text-amber-400 font-mono font-bold")
                        ui.label(f"Tokens: {res.total_tokens}").classes("text-[11px] text-slate-400")
                        ui.label("Cached for subsequent queries").classes("text-[11px] text-slate-400 italic")

        chat_scroll.scroll_to(percent=1.0)
        refresh_telemetry()
        refresh_cache_table()

    # Initial table population
    refresh_cache_table()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="Smart Support Concierge — Valkey Semantic Cache",
        port=8080,
        dark=True,
        reload=False,
    )
