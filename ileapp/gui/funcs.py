import os
from pathlib import Path

import PySimpleGUI as sg
from ileapp.globals import props


# initialize CheckBox control with module name
def CheckList(artifact, disable=False):
    # items in the if are modules that take a long time to run.
    # Deselects them by default.

    name, obj = props.installed_artifacts[artifact]
    mtxt = f'{obj.category} [{artifact}]'

    if obj.long_running_process:
        dstate = False
    else:
        dstate = True

    if obj.core_artifact is True:
        disable = True
        dstate = True
    return [sg.Checkbox(mtxt, default=dstate, key=f'-Artifact{artifact}-',
            metadata='{artifact}', disabled=disable, enable_events=True)]
