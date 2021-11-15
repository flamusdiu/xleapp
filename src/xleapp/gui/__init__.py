from __future__ import annotations

import logging
import re
import time
import typing as t
import webbrowser

from enum import Enum
from pathlib import Path

import PySimpleGUI as PySG

import xleapp.log as log
import xleapp.templating as templating

from xleapp.artifacts.services import ArtifactEnum

from ..artifacts import Artifacts
from ..helpers.search import search_providers
from ..helpers.strings import wraptext
from ..helpers.utils import ValidateInput
from .layout import error_popup_no_modules, generate_artifact_list, generate_layout
from .utils import ArtifactProcessor, disable_widgets


if t.TYPE_CHECKING:
    from xleapp.app import Application

regex = re.compile(r"^\w[\w\s]+\[(\w+)\]$")
window: PySG.Window = None
logger = logging.getLogger("xleapp.log")


def main(app: Application) -> None:
    """Main function for the GUI

    Args:
        app: application instance
    """

    # sets theme for GUI
    PySG.theme("DarkAmber")

    artifacts: t.Type[ArtifactEnum]
    device_type: str
    start_time: float = 0.0

    global window
    window = PySG.Window(
        f"xLEAPP Logs, Events, And Plists Parser - {app.version}",
        generate_layout(),
    ).finalize()

    if len(window["-DEVICETYPE-"].Values) > 0:
        device_type = app.device["Type"] = window["-DEVICETYPE-"].Values[0]
        artifacts = app.artifacts.data
        window["-DEVICETYPE-"].update(set_to_index=0, scroll_to_index=0)
        window["-MODULELIST-"].update(
            values=generate_artifact_list(artifacts),
            disabled=False,
        )
        window["-SELECTALL-"].update(disabled=False)
        window["-DESELECTALL-"].update(disabled=False)
        window.refresh()
    else:
        disable_widgets(window, disabled=True)
        window.refresh()

        error_popup_no_modules()
        window.close()

    processing, stop, done = False, False, False

    while True:
        event, values = window.read()

        if event in (PySG.WINDOW_CLOSE_ATTEMPTED_EVENT, "<CLOSE>", "<STOP>"):
            stop = True
        elif event == "-DEVICETYPE-" and values["-DEVICETYPE-"][0] != device_type:
            device_type = values["-DEVICETYPE-"][0]
            artifacts = Artifacts.generate_artifact_enum(app=app, device_type=device_type)
            modules = generate_artifact_list(artifacts=artifacts)
            window["-MODULELIST-"].update(modules)
            window["-MODULELIST-"].set_value(())
            window.refresh()
        elif event == "-SELECTALL-":
            modulelist = window["-MODULELIST-"].get_list_values()
            window["-MODULELIST-"].set_value(modulelist)
            window.refresh()
        elif event == "-DESELECTALL-":
            window["-MODULELIST-"].set_value(())
            window.refresh()
        elif event == "-PROCESS-":
            processing = True
            artifact_processor = ArtifactProcessor(app=app, window=window, daemon=True)

            disable_widgets(window, disabled=True)

            start_time = time.perf_counter()
            window["-PROCESS-"].update(disabled=True, visible=False)
            window["<STOP>"].update(visible=True)
            input_path = values["-INPUTFILEFOLDER-"]
            output_path = values["-OUTPUTFOLDER-"]

            ValidateInput(
                input_path=input_path,
                output_path=output_path,
            )

            app = app(
                device_type=values["-DEVICETYPE-"][0],
                input_path=input_path,
                output_path=output_path,
            )

            log.init()

            logger.info(f"Processing {app.num_to_process} artifacts...")
            artifact_processor.start()
        elif event == "<THREAD>":
            window["<PROGRESSBAR>"].update(values[event])
        elif event == "<DONE>":
            window.refresh()
            time.sleep(1)

            end_time = time.perf_counter()
            app.processing_time = end_time - start_time

            logger.info("\nGenerating index file...")
            templating.generate_index(app)
            logger.info("-> Index file generated!")

            app.generate_reports()

            report_path = Path(app.report_folder / "index.html").resolve()
            str_report_path = str(report_path).replace("\\\\", "\\")
            str_report_path = wraptext(str_report_path, "\\")
            window["<OPEN REPORT>"].update(disabled=False, visible=True)
            window["<REPORT URL>"].update(str_report_path, visible=True)
            window["<STOP>"].update(visible=False)
            window["<RERUN>"].update(visible=True)
            PySG.Popup("Processing completed")

            done = True
        elif event == "<OPEN REPORT>":
            webbrowser.open_new_tab(f"{report_path}")
        elif event == "<RERUN>":
            disable_widgets(window, False)
            window["<RERUN>"].update(visible=False)
            window["-PROCESS-"].update(visible=True)
            window["<PROGRESSBAR>"].update(0)
            window["<LOG>"].update("")

        if stop and done:
            break

        if stop:
            if artifact_processor.is_alive():
                logger.info("Stopping processing artifacts!")
                artifact_processor.join(1)
            if event != "<STOP>":
                break
            logger.info("Program Termindated!")
            window["<STOP>"].update(visible=False)
            window["<RERUN>"].update(visible=True)
            del app.artifacts
            app.seeker.clear()
            processing, stop = False, False

        if not processing:
            window["-PROCESS-"].update(disabled=(len(window["-MODULELIST-"].get()) == 0))

    window.close()
