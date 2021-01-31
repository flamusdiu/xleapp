import re
import sys
import traceback
import webbrowser
from pathlib import Path

import ileapp.artifacts as artifacts
import ileapp.gui.guiWindow as guiWindow
import PySimpleGUI as sg
from ileapp.globals import props
from ileapp.gui.funcs import ValidateInput
from ileapp.helpers import is_platform_windows

num_of_artifacts = len(props.installed_artifacts)
regex = re.compile(r'-Artifact(\w+)-')

# Select all artifacts
props.selected_artifacts.update(props.artifact_list)
props.artifact_list.clear()

def main(): # noqa C901
    window = guiWindow.window
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()

        if event in (None, 'Close'):   # if user closes window or clicks cancel
            break

        if regex.match(event):
            match = regex.match(event)
            name = match.group(1)
            if values[event] is True:
                props.select_artifact(name)
            else:
                props.deselect_artifact(name)

        elif event == "SELECT ALL":
            # mark all modules
            for name in list(props.artifact_list):
                window[f'-Artifact{name}-'].update(True)
                props.select_artifact(name)

        elif event == "DESELECT ALL":
            # none modules
            for name in list(props.selected_artifacts):
                if (window[f'-Artifact{name}-'].metadata != '-LastBuild'
                        or window[f'-Artifact{name}-'].metadata != 'ITunesBackupInfo'):
                    window[f'-Artifact{name}-'].update(False)  # lastBuild.py is REQUIRED
                    props.deselect_artifact(name)

        elif event == 'Process':
            # check is selections made properly; if not we will return to input
            # form without exiting app altogether
            extracttype, msg = ValidateInput(**values[:2], props.selected_artifact)

            if extracttype:
                input_path = Path(values[0])
                props.run_time_info['report_folder_base'] = Path(values[1])

                for name in list(props.installed_artifacts):
                    window[f'-Artifact{name}-'].update(disabled=True)

                window['SELECT ALL'].update(disabled=True)
                window['DESELECT ALL'].update(disabled=True)

                crunch_successful = (
                    artifacts.crunch_artifacts(
                        props.selected_artifacts,
                        extracttype,
                        input_path,
                        props.report_folder,
                        num_of_artifacts / len(props.selected_artifacts)
                    )
                )

                if crunch_successful:
                    report_path = props.report_folder / 'index.html'

                    locationmessage = f'Report name: {report_path}'
                    sg.Popup('Processing completed', locationmessage)
                    webbrowser.open_new_tab(f'file://{report_path}')
                else:
                    log_path = props.run_time_info['log_folder']
                    sg.popup_error('Processing failed    :( ',
                                   f'See log for error details..\nLog file located '
                                   f'at {log_path}')
                break
            elif msg:
                sg.popup_error(msg)

    window.close()
