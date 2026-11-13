import argparse
import asyncio
import socket
import subprocess
import sys

from nicegui import app, ui

from neuroml.utils import get_summary


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="nC2",
        description="neuroConstruct2: view and build neuronal models",
    )
    parser.add_argument(
        "model_file",
        help="Path to the model file to load (e.g. a NeuroML2 .net.nml file)",
    )
    parser.add_argument(
        "-nogui",
        "--nogui",
        action="store_true",
        default=False,
        help="Load the model but don't open the GUI window (e.g. for testing)",
    )
    return parser.parse_args(argv)


def open_3d_view(model_file):
    """Open the PyVista viewer for model_file in a separate window.

    plotter.show() needs the main thread, which pywebview already uses in native
    mode, so the viewer runs as a separate process.
    """
    subprocess.Popen(
        [sys.executable, "-m", "neuroConstruct2.neuromlmodel", str(model_file)]
    )
    ui.notify(f"Opening 3D view of {model_file}...")


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


async def show_embedded_view(model_file, container):
    """Serve the PyVista view via trame (separate process, see trame_view.py)
    and embed it in container as an iframe."""
    container.clear()
    with container:
        with ui.row().classes("items-center"):
            ui.spinner()
            ui.label(f"Loading 3D view of {model_file}...")

    port = _free_port()
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "neuroConstruct2.trame_view",
            str(model_file),
            "--port",
            str(port),
        ]
    )
    app.on_shutdown(proc.terminate)

    # wait for the trame server to come up (loading a big model can take a while)
    for _ in range(600):
        if proc.poll() is not None:
            break
        try:
            _, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.close()
            break
        except OSError:
            await asyncio.sleep(0.5)

    container.clear()
    with container:
        if proc.poll() is not None:
            ui.label(f"3D view failed to start (exit code {proc.returncode})")
            return
        ui.element("iframe").props(f'src="http://127.0.0.1:{port}/index.html"').style(
            "width: 100%; height: calc(100vh - 230px); border: 0"
        )


def main(model_file=None, nogui=False):
    # Console entry point (nC2): NiceGUI's native mode re-imports the main module
    # in a child process, which needs the __main__/__mp_main__ guard below. The
    # nC2 script doesn't have it, so run this module with `python -m` instead.
    if model_file is None:
        sys.exit(
            subprocess.call(
                [sys.executable, "-m", "neuroConstruct2.main"] + sys.argv[1:]
            )
        )

    # set the title of the nicegui window
    ui.label("neuroConstruct2").style(
        "font-size: 18px; font-weight: bold; margin-bottom: 20px;"
    )

    with ui.tabs().classes("w-full") as tabs:
        model = ui.tab("Model info")
        instance = ui.tab("Instance")
        three_d = ui.tab("3D View")

    with ui.tab_panels(tabs, value=instance).classes("w-full") as panels:
        with ui.tab_panel(model):
            ui.label(f"Model file: {model_file}").style(
                "font-size: 14px; margin-bottom: 10px;"
            )

        with ui.tab_panel(instance):
            ui.label("Instance info")
            model_info = get_summary(model_file)
            print(model_info)  # print to console for debugging

            # Add a button with label info
            info_html = model_info.replace("\n", "<br>")
            ui.button(
                "Info",
                on_click=lambda: ui.html(f"<pre>{info_html}</pre>"),
            )

        with ui.tab_panel(three_d):
            ui.button(
                "Open in separate window",
                on_click=lambda: open_3d_view(model_file),
            )
            view_container = ui.column().classes("w-full")

    # build the embedded 3D view the first time the tab is shown: loading is slow
    started = []

    async def on_tab_change(e):
        if e.value in (three_d, "3D View") and not started:
            started.append(True)
            await show_embedded_view(model_file, view_container)

    panels.on_value_change(on_tab_change)

    if nogui:
        print(f"Loaded {model_file}; not opening GUI (-nogui)")
        return

    ui.run(
        native=True, window_size=(1000, 700)
    )  # remove native=True to serve it as a web app


if __name__ in {"__main__", "__mp_main__"}:
    args = parse_args()
    main(args.model_file, args.nogui)
