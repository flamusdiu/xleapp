# xLEAPP

Framework for Logs, Events, And Plists Parser (LEAPP)

This framework is a complete rewrite of the excellent tool iLEAPP.Details of iLEAPP can be found in this blog post here: https://abrignoni.blogspot.com/2019/12/xleapp-ios-logs-events-and-properties.html

xLEAPP is the framework created to merge several tools together. More information about the rewrite is given in by talk at Black Hills Info Security's Wild West Hackin' Fest (WWHF): Deadwood in 2021: https://www.youtube.com/watch?v=seTpCmSF0Gc

## Features

* Provides a centralized and modular framework
* Provides a simplified way to write plugins (artifacts) for each different supported platform.
* Parses iOS, macOS, Android, Chromebook, warranty returns, and Windows artifacts depending on the plugins installed.

## Pre-requisites

This project requires you to have Python > 3.9

## Installation from github

```bash
# Create a project directory
$ mkdir xleapp-project
$ cd xleapp-project

# Clone the xLEAPP main repo
$ git clone https://github.com/flamusdiu/xleapp.git
$ python -m pip install .\xleapp

# Clone each plugin repo
$ git clone https://github.com/flamusdiu/xleapp-ios.git
$ python -m pip install .\xleapp-ios

# Run application
$ xleapp -h
usage: xleapp [-h] [-I] [-R] [-A] [-C] [-V] [-o OUTPUT_FOLDER] [-i INPUT_PATH] [--artifact [ARTIFACT ...]]
              [-p] [-l] [--gui] [--version]
```

## Installation for development

**Folder Structure**

If you follow all the information, you should end up with the following folders.

```txt
--| xleapp-project
       --| .vscode
       --| xleapp
       --| xleapp-ios
       --| xleapp-ios-non-free
       --| <other plugins>
```

To run this current development application, you need to do the following to setup the environment:

```bash
# Clone repo with VS Code configurations. Or alternatively,
# make a "xleapp-project" folder and skip this command.
$ git clone https://github.com/flamusdiu/xleapp-project.git

# Change directory into this folder
$ cd xleapp-project

# Clone the xLEAPP main repo
$ git clone https://github.com/flamusdiu/xleapp.git

# You will need some plugins. Do one more more of 
# the following. More will be added later!
$ git clone https://github.com/flamusdiu/xleapp-ios.git
$ git clone https://github.com/flamusdiu/xleapp-ios-non-free.git

# You need to change directory into the `xleapp` folder.
$ cd .\xleapp

# Create a virtual environment
$ python -m venv .venv

# Activate virtual environment
$ source .venv/Scripts/activate

# Then run the following This uses `pip` to install 
# the application. `-e` creates and editable installation. 
# See: https://pip.pypa.io/en/latest/cli/pip_install/#editable-installs on how this works.
$ python -m pip install -e .

# Add plugins (do not change folders)
$ python -m pip install -e ..\xleapp-ios
$ python -m pip install -e ..\xleapp-ios-non-free
$ python -m pip install -e ..\<plugin folder>
# do this for each plugin folder

# run the following:
$ (.venv) > xleapp -h # or > python -m xleapp -h
usage: xleapp [-h] [-I] [-R] [-A] [-C] [-V] [-o OUTPUT_FOLDER] [-i INPUT_PATH] [--artifact [ARTIFACT ...]]
              [-p] [-l] [--gui] [--version]

# Install development requirements
$ python -m pip install -r requirements-dev.txt

```

## VS Code configuration files

There are several configuration files that I have been using for VS Code. You can find those here: https://github.com/flamusdiu/xleapp-project


## Compile to executable

**NOTE:** This may not work at this time with this alpha version. 

To compile to an executable so you can run this on a system without python installed.

To create xleapp.exe, run:

```
pyinstaller --onefile xleapp.spec
````

To create xleappGUI.exe, run:

```
pyinstaller --onefile --noconsole xleappGUI.spec
```

## Usage

### CLI

```
$ xleapp -h
usage: xleapp [-h] [-I] [-R] [-A] [-C] [-V] [-o OUTPUT_FOLDER] [-i INPUT_PATH] [--artifact [ARTIFACT ...]]
              [-p] [-l] [--gui] [--version]

xLEAPP: Logs, Events, and Plists Parser.

optional arguments:
  -h, --help            show this help message and exit
  -I                    parse ios artifacts
  -R                    parse warranty return artifacts
  -A                    parse android artifacts
  -C                    parse Chromebook artifacts
  -V                    parse vehicle artifacts
  -o OUTPUT_FOLDER, --output_folder OUTPUT_FOLDER
                        Output folder path
  -i INPUT_PATH, --input_path INPUT_PATH
                        Path to input file/folder
  --artifact [ARTIFACT ...]
                        Filtered list of artifacts to run. Allowed: core, <check artifact list in
                        documentation>
  -p, --artifact_paths  Text file list of artifact paths
  -l, --artifact_table  Text file with table of artifacts
  --gui                 Runs xLEAPP into graphical mode
  --version             show program&#39;s version number and exit

```

### GUI

This needs work and may not work properly!

```
$ xleapp --gui 
```

### Help

```
$ xleapp.py --help
```

The GUI will open in another window.  <br><br>


## Acknowledgements

This tool is the result of a collaborative effort of many people in the DFIR community.

This product includes software developed by Sarah Edwards (Station X Labs, LLC, @iamevltwin, mac4n6.com) and other contributors as part of APOLLO (Apple Pattern of Life Lazy Output'er).
