import argparse
import os
from sys import argv, exit

from gui.gui import main_gui
from tools.ilapfuncs import is_platform_windows
from tools.properities import props


def main():
    """Main application entry point for CLI
    """
    parser = argparse.ArgumentParser(description='iLEAPP: iOS Logs, Events, and Plists Parser.')
    parser.add_argument('-t', choices=['fs', 'tar', 'zip', 'gz', 'itunes'], required=False, action="store", help="Input type (fs = extracted to file system folder)")
    parser.add_argument('-o', '--output_path', required=False, action="store", help='Output folder path')
    parser.add_argument('-i', '--input_path', required=False, action="store", help='Path to input file/folder')
    parser.add_argument('-p', '--artifact_paths', required=False, action="store_true", help='Text file list of artifact paths')
    parser.add_argument('-l', '--artifact_table', required=False, action="store_true", help='Text file with table of artifacts')

    args = parser.parse_args()

    if len(argv) == 1:
        main_gui()
    elif args.artifact_paths is True:
        pass
        # artifacts.generate_artifact_path_list()
    elif args.artifact_table is True:
        pass
        # artifacts.generate_artifact_table()
    else:
        input_path = args.input_path
        extracttype = args.t

        if args.output_path is None:
            parser.error('No OUTPUT folder path provided')
            exit(1)
        else:
            output_path = os.path.abspath(args.output_path)

        if output_path is None:
            parser.error('No OUTPUT folder selected. '
                         'Run the program again.')
            exit(1)

        if input_path is None or args.t is None:
            parser.error('No INPUT file or folder selected. '
                         'Run the program again.')
            exit(1)

        if not os.path.exists(input_path):
            parser.error('INPUT file/folder does not exist!'
                         'Run the program again.')
            exit(1)

        if not os.path.exists(output_path):
            parser.error('OUTPUT folder does not exist! '
                         'Run the program again.')
            exit(1)

        # ios file system extractions contain paths > 260 char,
        # which causes problems. This fixes the problem by
        # prefixing \\?\ on each windows path.
        if is_platform_windows():
            if input_path[1] == ':' and extracttype == 'fs':
                input_path = '\\\\?\\' + input_path.replace('/', '\\')
            if output_path[1] == ':':
                output_path = '\\\\?\\' + output_path.replace('/', '\\')

        props.output_parameters(output_path)
        # artifacts.crunch_artifacts(extracttype, input_path, 1)
