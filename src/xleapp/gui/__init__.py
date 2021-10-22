import logging
import re
import typing as t
import webbrowser

from pathlib import Path
from sre_constants import error

import PySimpleGUI as PySG

from PySimpleGUI.PySimpleGUI import (
    BUTTON_TYPE_CLOSES_WIN,
    BUTTON_TYPE_CLOSES_WIN_ONLY,
    Text,
)

import xleapp.gui.logging as gui_log
import xleapp.log as log

from xleapp.__main__ import _main
from xleapp.artifacts.services import Artifacts
from xleapp.helpers.utils import ValidateInput

from .layout import error_popup_no_modules, generate_artifact_list, generate_layout


if t.TYPE_CHECKING:
    from xleapp.app import XLEAPP

regex = re.compile(r"^\w[\w\s]+\[(\w+)\]$")

num_of_artifacts: int = 0

window: PySG.Window = None


def close_window(event):
    window.close()


def main(app: "XLEAPP") -> None:

    # sets theme for GUI
    PySG.theme("DarkAmber")

    artifacts: "Artifacts" = None
    device_type: str = None

    global window, valid_input
    window = PySG.Window(
        f"xLEAPP Logs, Events, And Plists Parser - {app.version}",
        generate_layout(),
    ).finalize()

    # Binds function to close button.
    window["<CLOSE>"].Widget.bind("<Button-1>", close_window)

    if len(window["-DEVICETYPE-"].Values) > 0:
        device_type = window["-DEVICETYPE-"].Values[0]
        artifacts = Artifacts.generate_artifact_enum(app=app, device_type=device_type)
        window["-DEVICETYPE-"].update(set_to_index=0, scroll_to_index=0)
        window["-MODULELIST-"].update(
            values=generate_artifact_list(artifacts),
            disabled=False,
        )
        window["-SELECTALL-"].update(disabled=False)
        window["-DESELECTALL-"].update(disabled=False)
        window.refresh()
    else:
        for widget in window.key_dict.keys():
            if str(widget).startswith("-") and str(widget).endswith("-"):
                try:
                    window[f"{widget}"].update(disabled=True)
                except TypeError:
                    # Widget does not have an update function. Just skip it.
                    pass

        window.refresh()

        error_popup_no_modules()
        window.close()

    while True:
        event, values = window.read()

        if event == PySG.WIN_CLOSED:
            break

        if "-DEVICETYPE-" in values and values["-DEVICETYPE-"][0] != device_type:
            device_type = values["-DEVICETYPE-"][0]
            artifacts = Artifacts.generate_artifact_enum(app=app, device_type=device_type)
            modules = generate_artifact_list(artifacts=artifacts)
            window["-MODULELIST-"].update(modules)
            window["-MODULELIST-"].set_value(())

        if event == "-SELECTALL-":
            modulelist = window["-MODULELIST-"].get_list_values()
            window["-MODULELIST-"].set_value(modulelist)
            window.refresh()

        elif event == "-DESELECTALL-":
            window["-MODULELIST-"].set_value(())
            window.refresh()

        elif event == "-PROCESS-":
            # check is selections made properly; if not we
            # will return to input form without exiting
            # app altogether

            # log.init()

            # logging.getLogger("xleapp.log").addHandler(gui_log.Handler())

            for artifact in app.artifacts:
                window[f"-Artifact{artifact.name}-"].update(disabled=True)

            input_path = values["-INPUTFILEFOLDER-"]
            output_folder = values["-OUTPUTFOLDER-"]

            extraction_type = ValidateInput(
                input_path=input_path,
                output_folder=output_folder,
            )
            app = app(
                device_type=values["-DEVICETYPE-"][0],
                input_path=input_path,
                output_folder=output_folder,
                extraction_type=extraction_type,
            )
            _main(app)

            report_path = Path(app.report_folder / "index.html").resolve()

            locationmessage = f"Report name: {report_path}"
            PySG.Popup("Processing completed", locationmessage)
            webbrowser.open_new_tab(f"{report_path}")
            break

        window["-PROCESS-"].update(disabled=(len(window["-MODULELIST-"].get()) == 0))

    window.close()
