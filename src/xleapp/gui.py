import logging
import re
import webbrowser
from pathlib import Path

import PySimpleGUI as PySG

import xleapp.artifacts as artifacts
import xleapp.globals as g
from xleapp.__main__ import _main


class Handler(logging.StreamHandler):
    def __init__(self):
        logging.StreamHandler.__init__(self)
        self.setLevel(logging.INFO)

    def emit(self, record):
        global buffer
        record = f"{record.name}, [{record.levelname}], {record.message}"
        buffer = f"{buffer}\n{record}".strip()
        window["-LOG-"].update(value=buffer)


regex = re.compile(r"-Artifact(\w+)-")

artifact_list: dict = {}
num_of_artifacts: int = 0
buffer: str = ""
window: PySG.Window = None


def generate_layout(artifact_full_list: list) -> list:
    num_of_artifacts = len(artifact_list)
    mlist = [checklist(artifact) for artifact in sorted(artifact_full_list.items())]
    normal_font = ("Helvetica", 12)

    layout = [
        [PySG.Text("iOS Logs, Events, And Plists Parser", font=("Helvetica", 22))],
        [PySG.Text("https://github.com/abrignoni/xLEAPP", font=("Helvetica", 14))],
        [
            PySG.Frame(
                layout=[
                    [
                        PySG.Input(size=(97, 1)),
                        PySG.FileBrowse(
                            font=normal_font,
                            button_text="Browse File",
                            key="-INPUTFILEBROWSE-",
                        ),
                        PySG.FolderBrowse(
                            font=normal_font,
                            button_text="Browse Folder",
                            target=(PySG.ThisRow, -2),
                            key="-INPUTFOLDERBROWSE-",
                        ),
                    ],
                ],
                title=(
                    "Select the file type or directory of the"
                    "target iOS full file system extraction"
                    "for parsing:"
                ),
            ),
        ],
        [
            PySG.Frame(
                layout=[
                    [
                        PySG.Input(size=(112, 1)),
                        PySG.FolderBrowse(
                            font=normal_font,
                            button_text="Browse Folder",
                        ),
                    ],
                ],
                title="Select Output Folder:",
            ),
        ],
        [PySG.Text("Available Modules")],
        [PySG.Button("SELECT ALL"), PySG.Button("DESELECT ALL")],
        [
            PySG.Column(
                mlist, size=(300, 310), scrollable=True, vertical_scroll_only=True
            ),
            PySG.Output(size=(85, 20), key="-LOG-"),
        ],
        [
            PySG.ProgressBar(
                max_value=num_of_artifacts,
                orientation="h",
                size=(86, 7),
                key="-PROGRESSBAR-",
                bar_color=("Red", "White"),
            ),
        ],
        [
            PySG.Submit("Process", font=normal_font),
            PySG.Button("Close", font=normal_font),
        ],
    ]
    return layout


# initialize CheckBox control with module name
def checklist(artifact, disable=False):
    # items in the if are modules that take a long time to run.
    # Deselects them by default.

    name, obj = artifact
    mtxt = f"{obj.category} [{name}]"
    obj.selected = dstate = not obj.long_running_process
    disable = obj.core

    return [
        PySG.Checkbox(
            mtxt,
            default=dstate,
            key=f"-Artifact{name.upper()}-",
            metadata="{name}",
            disabled=disable,
            enable_events=True,
        ),
    ]


def set_progress_bar(value: int) -> None:
    """Sets the progress bar for the GUI

    Args:
        value (int): how much progress is on the bar
    """
    window["-PROGRESSBAR-"].update_bar(value)


def main(alist: dict) -> None:
    artifact_list = alist

    # sets theme for GUI
    PySG.theme("DarkAmber")

    window = PySG.Window(f"{g.__version__}", generate_layout(artifact_list))

    logging.getLogger(__name__).addHandler(Handler())

    while True:
        event, values = window.read()

        if event in (None, "Close"):  # if user closes window or clicks cancel
            break

        if regex.match(event):
            match = regex.match(event)
            name = match.group(1)
            if values[event]:
                artifacts.select(artifact_list, name.lower())

        elif event == "SELECT ALL":
            for name in list(artifact_list):
                window[f"-Artifact{name.upper()}-"].update(True)
                artifacts.select(artifact_list, name.lower())

        elif event == "DESELECT ALL":
            for name, obj in artifact_list.items():
                if not obj.core:
                    window[f"-Artifact{name.upper()}-"].update(False)
                    artifacts.select(artifact_list, name.lower())

        elif event == "Process":
            # check is selections made properly; if not we
            # will return to input form without exiting
            # app altogether

            for name in list(artifact_list):
                window[f"-Artifact{name.upper()}-"].update(disabled=True)
            input_path = values[0]
            output_folder = values[1]

            _main(artifact_list, input_path, output_folder)

            report_path = Path(g.report_folder / "index.html").resolve()

            locationmessage = f"Report name: {report_path}"
            PySG.Popup("Processing completed", locationmessage)
            webbrowser.open_new_tab(f"{report_path}")
            break

    window.close()
