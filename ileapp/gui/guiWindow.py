import logging

import PySimpleGUI as sg
from gui.funcs import CheckList
from gui.guiLayout import generate_layout
from helpers.properties import props
from helpers.version_info import aleapp_version

window = sg.Window(f'iLEAPP version {aleapp_version}',
                   generate_layout(props.artifact_list))

# save the window handle
props.run_time_info('window_handle', window)


class Handler(logging.StreamHandler):
    def __init__(self):
        logging.StreamHandler.__init__(self)

    def emit(self, record):
        global buffer
        record = f'{record.name}, [{record.levelname}], {record.message}'
        buffer = f'{buffer}\n{record}'.strip()
        window['log'].update(value=buffer)


def generate_layout(artifact_list):
    mlist = [CheckList(artifact) for artifact in artifact_list.items()]
    normal_font = ("Helvetica", 12)

    layout = [[sg.Text('iOS Logs, Events, And Plists Parser',
               font=("Helvetica", 22))],
              [sg.Text('https://github.com/abrignoni/iLEAPP',
               font=("Helvetica", 14))],
              [sg.Frame(layout=[
                            [sg.Input(size=(97, 1)),
                             sg.FileBrowse(font=normal_font,
                                           button_text='Browse File',
                                           key='-INPUTFILEBROWSE-'),
                             sg.FolderBrowse(font=normal_font,
                                             button_text='Browse Folder',
                                             target=(sg.ThisRow, -2),
                                             key='-INPUTFOLDERBROWSE-')
                             ]
                            ],
                        title=('Select the file type or directory of the'
                               'target iOS full file system extraction'
                               'for parsing:'))
               ],
              [sg.Frame(layout=[
                           [sg.Input(size=(112, 1)),
                            sg.FolderBrowse(font=normal_font,
                            button_text='Browse Folder')]
                            ],
                        title='Select Output Folder:')],
              [sg.Text('Available Modules')],
              [sg.Button('SELECT ALL'), sg.Button('DESELECT ALL')],
              [sg.Column(mlist, size=(300, 310), scrollable=True),
               sg.Output(size=(85, 20))],
              [sg.ProgressBar(max_value=props.run_time,
               orientation='h', size=(86, 7), key='-PROGRESSBAR-',
               bar_color=('Red', 'White'))],
              [sg.Submit('Process', font=normal_font),
               sg.Button('Close', font=normal_font)]]
    return layout
