"""Serve the PyVista view of a NeuroML model over trame, for embedding in an iframe.

Run as a separate process (python -m neuroConstruct2.trame_view <file> --port N):
trame runs its own asyncio loop and the PyVista/VTK render window is happiest in
its own process, so this is kept apart from the NiceGUI app.
"""

import argparse

import pyvista as pv
from pyvista.trame.ui import plotter_ui
from trame.app import get_server
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vuetify3

from neuroConstruct2.neuromlmodel import build_plotter


def serve(model_file, port):
    pv.OFF_SCREEN = True
    plotter = build_plotter(model_file)

    # must be the default server: pyvista's plotter_ui attaches its view to it
    server = get_server(client_type="vue3")
    with SinglePageLayout(server) as layout:
        # Hide trame's toolbar/footer/padding so only the 3D view shows in the iframe
        layout.toolbar.hide()
        layout.footer.hide()
        with layout.content:
            with vuetify3.VContainer(fluid=True, classes="pa-0 fill-height"):
                plotter_ui(plotter, mode="server")

    server.start(port=port, open_browser=False, show_connection_info=False)


def main():
    parser = argparse.ArgumentParser(description="Serve a NeuroML 3D view via trame")
    parser.add_argument("model_file")
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    serve(args.model_file, args.port)


if __name__ == "__main__":
    main()
