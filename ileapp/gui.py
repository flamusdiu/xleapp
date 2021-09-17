import logging
import re
import webbrowser
from pathlib import Path

import PySimpleGUI as sg

import ileapp.artifacts as artifacts
import ileapp.ilapglobals as g
from ileapp.artifacts import artifact_list
from ileapp.helpers import ValidateInput

num_of_artifacts = len(artifacts.artifact_list)
regex = re.compile(r'-Artifact(\w+)-')

artifacts.select(all_artifacts=True)


# initialize CheckBox control with module name
def CheckList(artifact, disable=False):
    # items in the if are modules that take a long time to run.
    # Deselects them by default.

    name, obj = artifact_list[artifact]
    mtxt = f'{obj.category} [{artifact}]'

    if obj.long_running_process:
        dstate = False
    else:
        dstate = True

    if obj.core_artifact is True:
        disable = True
        dstate = True
    return [
        sg.Checkbox(
            mtxt,
            default=dstate,
            key=f'-Artifact{artifact}-',
            metadata='{artifact}',
            disabled=disable,
            enable_events=True,
        )
    ]


class Handler(logging.StreamHandler):
    def __init__(self):
        logging.StreamHandler.__init__(self)

    def emit(self, record):
        global buffer
        record = f'{record.name}, [{record.levelname}], {record.message}'
        buffer = f'{buffer}\n{record}'.strip()
        window['log'].update(value=buffer)


def set_progress_bar(val):
    """Sets the progress bar for the GUI

    Args:
        val (int): how much progress is on the bar
    """
    window = g.run_time_info['window_handle']
    window['-PROGRESSBAR-'].update_bar(val)


def generate_layout(artifact_list):
    mlist = [CheckList(artifact) for artifact in sorted(list(artifact_list))]
    normal_font = ("Helvetica", 12)

    layout = [
        [sg.Text('iOS Logs, Events, And Plists Parser', font=("Helvetica", 22))],
        [sg.Text('https://github.com/abrignoni/iLEAPP', font=("Helvetica", 14))],
        [
            sg.Frame(
                layout=[
                    [
                        sg.Input(size=(97, 1)),
                        sg.FileBrowse(
                            font=normal_font,
                            button_text='Browse File',
                            key='-INPUTFILEBROWSE-',
                        ),
                        sg.FolderBrowse(
                            font=normal_font,
                            button_text='Browse Folder',
                            target=(sg.ThisRow, -2),
                            key='-INPUTFOLDERBROWSE-',
                        ),
                    ]
                ],
                title=(
                    'Select the file type or directory of the'
                    'target iOS full file system extraction'
                    'for parsing:'
                ),
            )
        ],
        [
            sg.Frame(
                layout=[
                    [
                        sg.Input(size=(112, 1)),
                        sg.FolderBrowse(font=normal_font, button_text='Browse Folder'),
                    ]
                ],
                title='Select Output Folder:',
            )
        ],
        [sg.Text('Available Modules')],
        [sg.Button('SELECT ALL'), sg.Button('DESELECT ALL')],
        [sg.Column(mlist, size=(300, 310), scrollable=True), sg.Output(size=(85, 20))],
        [
            sg.ProgressBar(
                max_value=g.run_time_info['progress_bar_total'],
                orientation='h',
                size=(86, 7),
                key='-PROGRESSBAR-',
                bar_color=('Red', 'White'),
            )
        ],
        [sg.Submit('Process', font=normal_font), sg.Button('Close', font=normal_font)],
    ]
    return layout


def _process(input_path: str, output_path: str) -> bool:
    extracttype, msg = ValidateInput(
        input_path, output_path, artifacts.selected_artifact()
    )

    if extracttype:
        input_path = Path(input_path)
        g.run_time_info['report_folder_base'] = Path(output_path)

        for name in list(g.installed_artifacts):
            window[f'-Artifact{name}-'].update(disabled=True)

        window['SELECT ALL'].update(disabled=True)
        window['DESELECT ALL'].update(disabled=True)

        crunch_successful = artifacts.crunch_artifacts(
            artifact_list.selected_artifacts(),
            extracttype,
            input_path,
            g.run_time_info['report_folder'],
            num_of_artifacts / len(artifacts.selected_artifacts()),
        )

        return crunch_successful


def main(artifact_list):
    # Event Loop to process "events" and get the "values" of the inputs
    core_artifacts = set([name for name, artifact in artifact_list if artifact.core])
    while True:
        event, values = window.read()

        if event in (None, 'Close'):  # if user closes window or clicks cancel
            break

        if regex.match(event):
            match = regex.match(event)
            name = match.group(1)
            if values[event]:
                artifacts.select(name)

        elif event == "SELECT ALL":
            # mark all modules
            for name in list(artifact_list):
                window[f'-Artifact{name}-'].update(True)
                artifacts.select(name)

        elif event == "DESELECT ALL":
            # none modules
            for name in list(set(artifact_list) - core_artifacts):
                # lastBuild.py is REQUIRED
                window[f'-Artifact{name}-'].update(False)
                artifacts.select(name)

        elif event == 'Process':
            # check is selections made properly; if not we
            # will return to input form without exiting
            # app altogether

            crunch_successful = _process(**values[:2])

            if crunch_successful:
                report_path = g.run_time_info['report_folder'] / 'index.html'

                locationmessage = f'Report name: {report_path}'
                sg.Popup('Processing completed', locationmessage)
                webbrowser.open_new_tab(f'file://{report_path}')
            else:
                log_path = g.run_time_info['log_folder']
                sg.popup_error(
                    'Processing failed    :( ',
                    f'See log for error details..'
                    f'\nLog file located '
                    f'at {log_path}',
                )
                break

    window.close()


# sets theme for GUI
sg.theme('DarkAmber')

window = sg.Window(f'{g.VERSION}', generate_layout(artifact_list))

# save the window handle
g.run_time_info['window_handle'] = window
