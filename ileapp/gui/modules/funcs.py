import os
from pathlib import Path

import PySimpleGUI as sg
from ileapl.helpers.properities import props


def ValidateInput(values, window):
    """
    Returns tuple (success, extraction_type)
    """
    i_path = values[0]  # input file/folder
    o_path = values[1]  # output folder
    ext_type = ''

    if len(i_path) == 0:
        sg.PopupError('No INPUT file or folder selected!')
        return None
    elif not os.path.exists(i_path):
        sg.PopupError('INPUT file/folder does not exist!')
        return None
    elif (os.path.isdir(i_path) and os.path.exists(os.path.join(i_path,
          "Manifest.db"))):
        ext_type = 'itunes'
    elif os.path.isdir(i_path):
        ext_type = 'fs'
    else:  # must be an existing file then
        ext_type = Path(i_path).suffix[1:].lower()
        if ext_type not in ['tar', 'zip', 'gz']:
            sg.PopupError('Input file is not a supported archive! ', i_path)
            return None
        return ext_type

    # check output now
    if len(o_path) == 0:  # output folder
        sg.PopupError('No OUTPUT folder selected!')
        return None

    if len(props.selected_artifacts) == 0:
        sg.PopupError('No module selected for processing!')
        return None

    return ext_type


# initialize CheckBox control with module name
def CheckList(artifact, disable=False):
    # items in the if are modules that take a long time to run.
    # Deselects them by default.

    name, obj = artifact
    mtxt = f'{obj.cls.report_section} [{name}]'

    if obj.cls.long_running_process or name == 'LastBuild':
        dstate = True
    else:
        dstate = False

    if name == 'LastBuild':
        disable = True
    return [sg.Checkbox(mtxt, default=dstate, key=f'-{name}-',
            metadata=name, disabled=disable)]
