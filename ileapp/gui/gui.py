import os
import webbrowser

import artifacts
import PySimpleGUI as sg
from helpers.properities import props
from tools.ilapfuncs import is_platform_windows

from gui.modules.funcs import ValidateInput

# sets theme for GUI
sg.theme('DarkAmber')

num_of_artifacts = len(props.artifact_list)


def main_gui():
    window = props.run_time_information['window_handle']
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()
        if event in (None, 'Close'):   # if user closes window or clicks cancel
            break

        if event == "SELECT ALL":
            # mark all modules
            for name in props.artifact_list:
                window[name].update(True)

            props.selected_artifacts.update(props.artifact_list)
            props.artifact_list.clear()

        if event == "DESELECT ALL":
            # none modules
            for name in props.artifact_list:
                if window[name].metadata != 'LastBuild':
                    window[name].update(False)  # lastBuild.py is REQUIRED

                props.artifact_list.update(props.selected_artifacts)
                props.selected_artifacts.clear()

        if event == 'Process':
            # check is selections made properly; if not we will return to input
            # form without exiting app altogether
            is_valid, extracttype = ValidateInput(values, window)
            if is_valid:
                input_path = values[0]
                output_folder = values[1]

                # ios file system extractions contain paths > 260 char, which
                # causes problems. This fixes the problem by prefixing \\?\
                # on each windows path.
                if is_platform_windows():
                    if input_path[1] == ':' and extracttype == 'fs':
                        input_path = '\\\\?\\' + input_path.replace('/', '\\')
                    if output_folder[1] == ':':
                        output_folder = ('\\\\?\\' +
                                         output_folder.replace('/', '\\'))

                for name, artifact in props.artifact_list.items():
                    if window[name].Get():
                        props.select_artifact(name)

                    # no more selections allowed
                    window[name].update(disabled=True)

                window['SELECT ALL'].update(disabled=True)
                window['DESELECT ALL'].update(disabled=True)

                out_params = props.output_parameters
                crunch_successful = (
                    artifacts.crunch_artifacts(props.selected_artifacts,
                                               extracttype,
                                               input_path,
                                               out_params,
                                               num_of_artifacts/len(props.selected_artifacts)))
                if crunch_successful:
                    report_path = os.path.join(out_params.report_folder_base,
                                               'index.html')

                    if report_path.startswith('\\\\?\\'):  # windows
                        report_path = report_path[4:]
                    if report_path.startswith('\\\\'):  # UNC path
                        report_path = report_path[2:]
                    locationmessage = 'Report name: ' + report_path
                    sg.Popup('Processing completed', locationmessage)
                    webbrowser.open_new_tab('file://' + report_path)
                else:
                    log_path = out_params.screen_output_file_path
                    if log_path.startswith('\\\\?\\'):  # windows
                        log_path = log_path[4:]
                    sg.Popup('Processing failed    :( ',
                             f'See log for error details..\nLog file located '
                             f'at {log_path}')
                break
    window.close()
