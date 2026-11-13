import argparse

from nicegui import ui

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
    import subprocess
    import sys

    subprocess.Popen(
        [sys.executable, "-m", "neuroConstruct2.neuromlmodel", str(model_file)]
    )
    ui.notify(f"Opening 3D view of {model_file}...")


def main(model_file=None, nogui=False):
    # Console entry point (nC2): NiceGUI's native mode re-imports the main module
    # in a child process, which needs the __main__/__mp_main__ guard below. The
    # nC2 script doesn't have it, so run this module with `python -m` instead.
    if model_file is None:
        import subprocess
        import sys

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

    with ui.tab_panels(tabs, value=instance).classes("w-full"):
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
            ui.label("3D view of the model")
            ui.button(
                "Open 3D view",
                on_click=lambda: open_3d_view(model_file),
            )

    if nogui:
        print(f"Loaded {model_file}; not opening GUI (-nogui)")
        return

    ui.run(
        native=True, window_size=(1000, 700)
    )  # remove native=True to serve it as a web app


if __name__ in {"__main__", "__mp_main__"}:
    args = parse_args()
    main(args.model_file, args.nogui)
