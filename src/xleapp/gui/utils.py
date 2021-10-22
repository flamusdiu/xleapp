import xleapp.gui as gui


def set_progress_bar(value: int) -> None:
    """Sets the progress bar for the GUI

    Args:
        value (int): how much progress is on the bar
    """
    gui.window["-PROGRESSBAR-"].update_bar(value)
