import PySimpleGUI as PySG

import xleapp.gui as gui


def set_progress_bar(value: int) -> None:
    """Sets the progress bar for the GUI

    Args:
        value (int): how much progress is on the bar
    """
    gui.window["-PROGRESSBAR-"].update_bar(value)


def disable_widgets(window: PySG.Window, disabled: bool = False):
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
