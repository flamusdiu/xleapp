import logging
import re
import time
import typing as t
import webbrowser

from pathlib import Path
from threading import Thread

import PySimpleGUI as PySG

import xleapp.gui.log as gui_log
import xleapp.log as log
import xleapp.templating as templating

from xleapp.__main__ import _main
from xleapp.artifacts.services import Artifacts
from xleapp.gui.utils import disable_widgets
from xleapp.helpers.search import search_providers
from xleapp.helpers.strings import wraptext
from xleapp.helpers.utils import ValidateInput

from .layout import error_popup_no_modules, generate_artifact_list, generate_layout


if t.TYPE_CHECKING:
    from xleapp.app import XLEAPP

regex = re.compile(r"^\w[\w\s]+\[(\w+)\]$")
window: PySG.Window = None
logger = logging.getLogger("xleapp.log")


def main(app: "XLEAPP") -> None:

    # sets theme for GUI
    PySG.theme("DarkAmber")

    artifacts: "Artifacts" = None
    device_type: str = None
    start_time: float() = 0.0

    global window
    window = PySG.Window(
        f"xLEAPP Logs, Events, And Plists Parser - {app.version}",
        generate_layout(),
    ).finalize()
    window['<REPORT URL>'].expand(True)

    if len(window["-DEVICETYPE-"].Values) > 0:
        device_type = window["-DEVICETYPE-"].Values[0]
        artifacts = app.artifacts(device_type=device_type)
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

    artifact_processor = Thread(target=app.crunch_artifacts, args=(window,), daemon=True)
    window.refresh()

    processing, stop, done = False, False, False

    while True:
        event, values = window.read()

        if event in (PySG.WINDOW_CLOSE_ATTEMPTED_EVENT, "<CLOSE>"):
            stop = True
        elif "-DEVICETYPE-" in values and values["-DEVICETYPE-"][0] != device_type:
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

            disable_widgets(window, disabled=True)

            start_time = time.perf_counter()

            input_path = values["-INPUTFILEFOLDER-"]
            output_path = values["-OUTPUTFOLDER-"]

            extraction_type = ValidateInput(
                input_path=input_path,
                output_path=output_path,
            )

            app = app(
                device_type=values["-DEVICETYPE-"][0],
                input_path=input_path,
                output_path=output_path,
                extraction_type=extraction_type,
            )

            app.seeker = search_providers.create(
                app.extraction_type.upper(),
                directory=app.input_path,
                temp_folder=app.temp_folder,
            )

            log.init()
            window["<PROGRESSBAR>"].update(0, app.num_to_process)

            logger.info(f"Processing {app.num_to_process} artifacts...")
            artifact_processor.start()
        elif event == "<THREAD>":
            window["<PROGRESSBAR>"].update(values[event])
        elif event == "<DONE>":
            window.refresh()
            time.sleep(1)

            # logger.info(f"\nCompleted processing artifacts in {run_time:.2f}s")
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
            window['<REPORT URL>'].update(str_report_path, visible=True)
            PySG.Popup("Processing completed")

            done = True
        elif event == "<OPEN REPORT>":
            webbrowser.open_new_tab(f"{report_path}")

        if stop and done:
            break

        if not processing:
            window["-PROCESS-"].update(disabled=(len(window["-MODULELIST-"].get()) == 0))

    window.close()
