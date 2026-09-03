"""
NiceGUI Web Application interface for Valkey Semantic Cache Benchmark.
Provides interactive controls, live KPI tracking, streaming system-out logs,
and formatted system-out report rendering.
"""

import asyncio
from nicegui import ui, run
from typing import Optional

from cache_service import service
from .runner import run_benchmark, BenchmarkSummary
from .reporter import generate_stdout_report


def render_benchmark_ui():
    """
    Renders the Benchmark Suite UI components into the current NiceGUI container.
    """
    with ui.column().classes("w-full gap-4 p-2"):
        
        # -------------------------------------------------------------
        # TOP HEADER CARD
        # -------------------------------------------------------------
        with ui.card().classes("w-full bg-slate-800/90 border border-slate-700 p-4 rounded-xl shadow-lg"):
            with ui.row().classes("items-center justify-between w-full pb-2 border-b border-slate-700"):
                with ui.row().classes("items-center gap-3"):
                    ui.icon("speed", size="28px").classes("text-amber-400")
                    with ui.column().classes("gap-0"):
                        ui.label("Semantic Cache Benchmark Suite").classes("text-lg font-bold text-white tracking-wide")
                        ui.label("Automated telemetry benchmarking & system-out report generation").classes("text-xs text-slate-400")

                with ui.badge(color="primary").classes("px-3 py-1.5 text-xs font-mono"):
                    ui.label("Cloud Run Ready")

        # -------------------------------------------------------------
        # MAIN 2-COLUMN LAYOUT: CONTROLS (LEFT) & LIVE STATS (RIGHT)
        # -------------------------------------------------------------
        with ui.row().classes("w-full gap-4 items-start"):
            
            # --- LEFT: CONTROLS & PARAMETERS ---
            with ui.column().classes("w-[360px] gap-4"):
                with ui.card().classes("w-full bg-slate-800/90 border border-slate-700 p-4 rounded-xl shadow-lg gap-3"):
                    with ui.row().classes("items-center gap-2 pb-2 border-b border-slate-700"):
                        ui.icon("tune", size="20px").classes("text-indigo-400")
                        ui.label("Benchmark Parameters").classes("text-sm font-semibold text-white")

                    # Number of queries input
                    queries_slider = ui.slider(
                        min=10, max=1000, step=10, value=100
                    ).props("label label-always color=amber dark").classes("w-full pt-4")
                    with ui.row().classes("w-full justify-between items-center text-xs text-slate-300"):
                        ui.label("Total Queries:")
                        queries_val_lbl = ui.label("100 queries").classes("font-mono font-bold text-amber-400")

                    queries_slider.on(
                        "change",
                        lambda e: queries_val_lbl.set_text(f"{int(e.value)} queries"),
                    )

                    # Target Hit Rate slider
                    hit_rate_slider = ui.slider(
                        min=0.10, max=0.95, step=0.05, value=0.80
                    ).props("label label-always color=emerald dark").classes("w-full pt-4")
                    with ui.row().classes("w-full justify-between items-center text-xs text-slate-300"):
                        ui.label("Target Hit Rate:")
                        hit_rate_val_lbl = ui.label("80%").classes("font-mono font-bold text-emerald-400")

                    hit_rate_slider.on(
                        "change",
                        lambda e: hit_rate_val_lbl.set_text(f"{int(float(e.value) * 100)}%"),
                    )

                    # Execution mode selection
                    ui.label("Execution Mode:").classes("text-xs font-semibold text-slate-300 pt-2")
                    mode_select = ui.select(
                        options={
                            "mock": "⚡ Mock Mode (Fast Simulation)",
                            "live": "🔴 Live Mode (Valkey + Vertex AI)",
                        },
                        value="mock",
                    ).props("outlined dense dark").classes("w-full bg-slate-900 text-xs")

                    # Clear cache checkbox
                    clear_cache_cb = ui.checkbox("Clear Valkey cache before starting", value=True).props("dark").classes("text-xs text-slate-300")

                    # Run / Stop Buttons
                    with ui.row().classes("w-full gap-2 pt-2 border-t border-slate-700"):
                        run_btn = ui.button("🚀 Run Benchmark", color="primary").props("no-caps").classes("flex-1 text-sm font-bold py-2 rounded-lg")
                        stop_btn = ui.button("⏹️ Reset", color="slate").props("outline dense no-caps").classes("text-xs text-slate-300")

            # --- RIGHT: LIVE TELEMETRY DASHBOARD & SYSTEM-OUT CONSOLE ---
            with ui.column().classes("flex-1 min-w-[500px] gap-4"):
                
                # Live KPI Cards
                with ui.card().classes("w-full bg-slate-800/90 border border-slate-700 p-4 rounded-xl shadow-lg"):
                    with ui.row().classes("items-center justify-between w-full pb-2 border-b border-slate-700"):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("analytics", size="20px").classes("text-sky-400")
                            ui.label("Real-Time Benchmark Telemetry").classes("text-sm font-semibold text-white")
                        progress_badge = ui.badge("Idle", color="slate").classes("px-2 py-0.5 text-xs font-mono")

                    # Progress Bar
                    progress_bar = ui.linear_progress(value=0.0, show_value=False).props("color=amber track-color=slate-700").classes("w-full my-2 rounded")

                    # 4 KPI Boxes
                    with ui.grid(columns=4).classes("w-full gap-3 pt-1"):
                        with ui.card().classes("bg-slate-900 p-3 rounded-lg border border-slate-700/60 text-center"):
                            queries_lbl = ui.label("0 / 0").classes("text-lg font-bold text-white font-mono")
                            ui.label("Queries Executed").classes("text-[10px] text-slate-400 uppercase tracking-wider")

                        with ui.card().classes("bg-slate-900 p-3 rounded-lg border border-slate-700/60 text-center"):
                            hit_rate_lbl = ui.label("0.0%").classes("text-lg font-bold text-emerald-400 font-mono")
                            ui.label("Cache Hit Rate").classes("text-[10px] text-slate-400 uppercase tracking-wider")

                        with ui.card().classes("bg-slate-900 p-3 rounded-lg border border-slate-700/60 text-center"):
                            tokens_lbl = ui.label("0").classes("text-lg font-bold text-amber-400 font-mono")
                            ui.label("Tokens Saved").classes("text-[10px] text-slate-400 uppercase tracking-wider")

                        with ui.card().classes("bg-slate-900 p-3 rounded-lg border border-slate-700/60 text-center"):
                            time_lbl = ui.label("0.0s").classes("text-lg font-bold text-sky-400 font-mono")
                            ui.label("Time Saved").classes("text-[10px] text-slate-400 uppercase tracking-wider")

                # System-Out Streaming Console Log
                with ui.card().classes("w-full bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-lg gap-2"):
                    with ui.row().classes("items-center justify-between w-full pb-2 border-b border-slate-800"):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("terminal", size="18px").classes("text-emerald-400")
                            ui.label("Live System-Out Console").classes("text-xs font-semibold text-slate-200 font-mono")
                        ui.button("Clear Log", on_click=lambda: console_log.clear()).props("flat dense color=slate-400 size=xs no-caps")

                    console_log = ui.log(max_lines=500).classes("w-full h-[220px] bg-slate-950 p-2 rounded border border-slate-800 font-mono text-[11px] text-emerald-300 leading-tight")

        # -------------------------------------------------------------
        # BOTTOM: SYSTEM-OUT FORMATTED REPORT CONTAINER
        # -------------------------------------------------------------
        with ui.card().classes("w-full bg-slate-800/90 border border-slate-700 p-4 rounded-xl shadow-lg gap-2 mt-2") as report_card:
            with ui.row().classes("items-center justify-between w-full pb-2 border-b border-slate-700"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("description", size="22px").classes("text-purple-400")
                    ui.label("System-Out Formatted Benchmark Report").classes("text-base font-bold text-white")
                ui.label("Nicely formatted ASCII tables output").classes("text-xs text-slate-400")

            report_display = ui.code("", language="markdown").classes("w-full max-h-[500px] overflow-auto bg-slate-950 p-4 rounded-lg font-mono text-xs text-slate-200 border border-slate-800 leading-relaxed")

    # -------------------------------------------------------------
    # EVENT HANDLERS & BENCHMARK THREAD EXECUTION
    # -------------------------------------------------------------
    async def start_benchmark_handler():
        total_q = int(queries_slider.value)
        target_r = float(hit_rate_slider.value)
        is_mock = (mode_select.value == "mock")
        clear_cache = clear_cache_cb.value

        run_btn.disable()
        progress_badge.text = "RUNNING..."
        progress_badge.props("color=amber")
        progress_bar.value = 0.0
        console_log.clear()

        # Update HUD state
        queries_lbl.text = f"0 / {total_q}"
        hit_rate_lbl.text = "0.0%"
        tokens_lbl.text = "0"
        time_lbl.text = "0.0s"
        report_display.set_content("Executing benchmark... Report will appear here upon completion.")

        def log_to_ui(msg: str):
            console_log.push(msg)

        def progress_to_ui(idx: int, total: int, item_res, summary_so_far):
            pct = idx / total
            progress_bar.value = pct
            queries_lbl.text = f"{idx} / {total}"
            hit_rate_lbl.text = f"{summary_so_far['hit_rate_pct']:.1f}%"
            tokens_lbl.text = f"{summary_so_far['tokens_saved']:,}"
            time_lbl.text = f"{(summary_so_far['time_saved_ms'] / 1000.0):.1f}s"

        # Execute run_benchmark in async thread pool
        try:
            summary, _ = await run.io_bound(
                run_benchmark,
                queries_count=total_q,
                target_hit_rate=target_r,
                mock_mode=is_mock,
                clear_cache_first=clear_cache,
                verbose=False,
                progress_callback=progress_to_ui,
                log_callback=log_to_ui,
            )

            # Generate formatted system-out report
            report_text = generate_stdout_report(summary)
            report_display.set_content(report_text)

            progress_badge.text = "COMPLETED"
            progress_badge.props("color=positive")
            ui.notify(f"Benchmark completed successfully! Hit rate: {summary.cache_hit_rate_pct:.1f}%", type="positive")
        except Exception as e:
            log_to_ui(f"\n❌ Benchmark Error: {str(e)}")
            progress_badge.text = "FAILED"
            progress_badge.props("color=negative")
            ui.notify(f"Benchmark failed: {str(e)}", type="negative")
        finally:
            run_btn.enable()

    def reset_handler():
        progress_bar.value = 0.0
        progress_badge.text = "Idle"
        progress_badge.props("color=slate")
        queries_lbl.text = "0 / 0"
        hit_rate_lbl.text = "0.0%"
        tokens_lbl.text = "0"
        time_lbl.text = "0.0s"
        console_log.clear()
        report_display.set_content("Run a benchmark to view the system-out formatted report.")

    run_btn.on_click(start_benchmark_handler)
    stop_btn.on_click(reset_handler)
