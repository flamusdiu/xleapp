from enum import Enum

import PySimpleGUI as sg


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


def disable_widgets(window, disabled):
    for widget in window.key_dict.keys():
        if str(widget).startswith("-") and str(widget).endswith("-"):
            try:
                window[f"{widget}"].update(
                    disabled=disabled,
                )
            except TypeError:
                # Widget does not have an update function. Just skip it.
                pass
    window.refresh()


sg.theme('DarkAmber')


layout_frame_1 = [
    [sg.In(size=98, key="-INPUTFILEFOLDER-", disabled_readonly_background_color="red"),
     sg.FileBrowse(font=Font.NORMAL, button_text="Browse File", key="-INPUTFILEBROWSER-", file_types=(("Compressed Files", ("*.tar", "*.zip", "*.gz")))),
     sg.FolderBrowse(font=Font.NORMAL, button_text="Browse Folder", key="-INPUTFOLDERBROWSER-", target=(sg.ThisRow, -2))]
]

layout_frame_2 = [
    [sg.In(size=113, key="-OUTPUTFOLDER-"), sg.FolderBrowse(font=Font.NORMAL, button_text="Browse Folder", key="-OUTPUTFOLDERBROWSER-")]
]

layout = [
    [sg.Frame(layout=layout_frame_1, title="Select the file type or directory of the target file for parsing:", font=Font.FRAME)],
    [sg.Frame(layout=layout_frame_2, title="Select Output Folder:", font=Font.FRAME)],
    [sg.Submit("Process", font=Font.NORMAL, disabled=True, key="-PROCESS-"),
     sg.Button("Close", font=Font.NORMAL, key="<CLOSE>"),
     sg.Col([[sg.Multiline(font=Font.NORMAL, key="<REPORT URL>", size=(70,2), no_scrollbar=True, disabled=True, enter_submits=False, write_only=True, visible=False)]], pad=(0,0)),
     sg.Button("Open Report", font=Font.NORMAL, key="<OPEN REPORT>", disabled=True, visible=False)],
    [sg.Button("Disabled On/Off"), sg.Button("Hide Multiline")],
    [sg.StatusBar("Input element not Disabled", key="-STATUS-")]
]

window = sg.Window("xLEAPP GUI Test", layout, finalize=True)

hidden, disabled = False, False

while True:

    event, values = window.read()

    if event == sg.WINDOW_CLOSED:
        break
    elif event == "Disabled On/Off":
        disabled = not disabled
        disable_widgets(window, disabled)
        window['-STATUS-'].update(f'Input element {"" if disabled else "not "}Disabled')
    elif event == "Hide Multiline":
        hidden = not hidden
        window["<REPORT URL>"].update(visible=hidden)
        window["<OPEN REPORT>"].update(visible=hidden)
        window["-STATUS-"].update(f'Multiline element {"" if not hidden else "not "}Hidden')

window.close()
