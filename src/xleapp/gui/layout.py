import re
import typing as t
import webbrowser

from enum import Enum

import PySimpleGUI as PySG

from PySimpleGUI import LISTBOX_SELECT_MODE_MULTIPLE, LISTBOX_SELECT_MODE_SINGLE

import xleapp.helpers.utils as utils


if t.TYPE_CHECKING:
    from xleapp.artifacts.services import Artifacts


class Font(Enum):
    URL = ("Helvetica", 12, "underline")
    NORMAL = ("Helvetica", 12)
    FRAME = ("Helvetica", 14, "bold")

    def __init__(self, font=None, size=12, styles=None):
        self.font = font
        self.size = size
        self.styles = styles

    def __repr__(self) -> str:
        return str(f"{self.font} {self.size} {self.styles}")


def get_title(device_type: str):
    pass


def generate_artifact_list(artifacts: "Artifacts"):
    return [
        f"{artifact.category} [{artifact.cls_name}]"
        for artifact in artifacts
        if not artifact.core
    ]


def generate_device_list():
    regex = re.compile(r"^(\w+)-?")
    plugins = utils.discovered_plugins()
    device_types = {
        regex.match(plugin).group(1) for plugin in plugins.keys() if regex.match(plugin)
    }
    return list(device_types)


# Disabled formatting from 'Black' so these PySG layouts are more compressed and
# easier to read.
# fmt: off
def layout_right_column():
    layout = [
        [PySG.Fr(
            layout=[
                [PySG.LBox(generate_device_list(), size=(20, 3), enable_events=True,
                 key='-DEVICETYPE-', select_mode=LISTBOX_SELECT_MODE_SINGLE)],
            ], title="Device Type", font=Font.FRAME)],
        [PySG.Fr(
            layout=[
                [PySG.B("SELECT ALL", disabled=True, key="-SELECTALL-"),
                 PySG.B("DESELECT ALL", disabled=True, key="-DESELECTALL-")],
                [PySG.LBox(values=[], select_mode=LISTBOX_SELECT_MODE_MULTIPLE,
                 key="-MODULELIST-", size=(42, 15), disabled=True, enable_events=True)],
            ], title="Available Modules", font=Font.FRAME)],
    ]

    return PySG.Col(layout, pad=((0, 2), (0, 0)))


def layout_left_column():
    layout = [
        [PySG.Fr(
            layout=[
                [PySG.Multiline(
                    size=(79, 23),
                    key="<LOG>",
                    reroute_stdout=True,
                    write_only=True,
                    autoscroll=True,
                )],
            ], title="Log File", font=Font.FRAME)],
    ]

    return PySG.Col(layout)


def generate_menu() -> list:
    menu_def = [["&Help", ["&Online Documentation...", "&About..."]]]
    return [PySG.Menu(menu_def, tearoff=False)]


def generate_layout() -> list:
    return [
        [generate_menu()],
        [
            PySG.Fr(
                layout=[[
                    PySG.In(
                        size=98,
                        key="-INPUTFILEFOLDER-",
                        disabled_readonly_background_color=(
                            PySG.theme_input_background_color()
                        ),
                    ),
                    PySG.FileBrowse(
                        font=Font.NORMAL,
                        button_text="Browse File", key="-INPUTFILEBROWSER-",
                        file_types=(("Compressed Files", ("*.tar", "*.zip", "*.gz")),),
                    ),
                    PySG.FolderBrowse(
                        font=Font.NORMAL,
                        button_text="Browse Folder", key="-INPUTFOLDERBROWSER-",
                        target=(PySG.ThisRow, -2),
                    ),
                ]],
                title=(
                    "Select the file type or directory of the target file for "
                    "parsing:"
                ),
                font=Font.FRAME),
        ],
        [
            PySG.Fr(
                layout=[[
                    PySG.In(
                        size=113,
                        key="-OUTPUTFOLDER-",
                        disabled_readonly_background_color=(
                            PySG.theme_input_background_color()
                        ),
                    ),
                    PySG.FolderBrowse(
                        font=Font.NORMAL,
                        button_text="Browse Folder",
                        key="-OUTPUTFOLDERBROWSER-",
                    ),
                ]],
                title="Select Output Folder:", font=Font.FRAME),
        ],
        [
            layout_right_column(),
            layout_left_column(),
        ],
        [
            PySG.PBar(
                max_value=0,
                orientation="h",
                size=(85, 7),
                key="<PROGRESSBAR>",
                bar_color=("Red", "White"),),
        ],
        [
            PySG.Submit(
                "Process",
                font=Font.NORMAL,
                disabled=True,
                key="-PROCESS-",
                size=(7, 1),
            ),
            PySG.B(
                "Close",
                font=Font.NORMAL,
                key="<CLOSE>",
                size=(5, 1),
            ),
            PySG.Col([[PySG.Multiline(
                font=Font.NORMAL,
                key="<REPORT URL>",
                size=(70, 2),
                no_scrollbar=True,
                disabled=True,
                enter_submits=False,
                write_only=True,
                visible=False,
            )]], pad=(0, 0)),
            PySG.B(
                "Open Report",
                font=Font.NORMAL,
                key="<OPEN REPORT>",
                disabled=True,
                visible=False,
            ),
        ],
    ]


def url(url: str, title: str) -> PySG.Text:
    return PySG.Text(
        title,
        tooltip=url,
        enable_events=True,
        font=Font.URL.value,
        key=f'-URL: {url}-',
        border_width=0,
    )


def error_popup_no_modules():
    dialog = PySG.Window(
        "Error!",
        [
            [PySG.Text('There are no plugins installed! Please see:',
                       font=Font.NORMAL,
                       border_width=0,),
             url(
                url="https://github.com/flamusdiu/xleapp#readme",
                title="xLEAPP Readme",)
             ],
            [PySG.Button('Error!', key="-ERROR-", button_color="Red", font=Font.NORMAL)],
        ], modal=True, disable_minimize=True, disable_close=True,
    )

    while True:
        event, values = dialog.read()

        if event == PySG.WIN_CLOSED:
            break

        if event.startswith("-URL: "):
            clicked_url = event.strip("-").split(" ")[1]
            webbrowser.open_new_tab(clicked_url)
        dialog.close()
# fmt: on
