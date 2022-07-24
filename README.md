# xLEAPP

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

**Development build. Please be cauious using on real cases.**

Framework for Logs, Events, And Plists Parser (LEAPP)

This framework is a complete rewrite of the excellent tool iLEAPP.Details of iLEAPP can be found in this [blog post](https://abrignoni.blogspot.com/2019/12/xleapp-ios-logs-events-and-properties.html)

xLEAPP is the framework created to merge several tools together. More information about the rewrite is given in by talk ([YouTube](https://www.youtube.com/watch?v=seTpCmSF0Gc)) at Black Hills Info Security&#39;s Wild West Hackin&#39; Fest (WWHF): Deadwood in 2021.

<img src="https://user-images.githubusercontent.com/1879197/139466769-3155b3d9-75c6-4ef0-bbb0-73b77fdc349f.gif" width=700>

## Features

* Provides a centralized and modular framework
* Provides a simplified way to write plugins (artifacts) for each different supported platform.
* Parses iOS, macOS, Android, Chromebook, warranty returns, and Windows artifacts depending on the plugins installed.

## Other Documentation

* [Artifact Creation](docs/current/artifact-creation.md)

## Pre-requisites

This project requires you to have Python >= 3.9

## Plugins

Here is a list of plugins that need to be completed. Plugin package suffixed with "non-free" use licenses that may not conform with MIT licenses and are seperated out.

- [X] xleapp-ios [[Github](https://github.com/flamusdiu/xleapp-ios)] [[PyPI](https://pypi.org/project/xleapp-ios/)]
- [ ] xleapp-ios-non-free [[Github](https://github.com/flamusdiu/xleapp-ios)]
- [ ] xleapp-android
- [ ] xleapp-android-non-free
- [ ] xleapp-chrome
- [ ] xleapp-chrome-non-free
- [ ] xleapp-returns
- [ ] xleapp-returns-non-free
- [ ] xleapp-vehicles
- [ ] xleapp-vehicles-non-free
- [ ] xleapp-windows
- [ ] xleapp-windows-non-free

## Installation

### Windows

* Python

  ```powershell
  PS> py -3 -m pip install xleapp
  PS> py -3 -m pip install xleapp-<plugin>
  ```

* PIPX

  ```powershell
  PS> py -3 -m pip install pipx
  PS> pipx install xleapp
  PS> pipx inject xleapp xleapp-<plugin>
  ```

### Linux

* Python

  ```bash
  $ python3 -m pip install xleapp
  $ python3 -m pip install xleapp-<plugin>
  ```

* PIPX

  ```bash
  $ python3 -m pip install pipx
  $ pipx install xleapp
  $ pipx inject xleapp xleapp-<plugin>
  ```

## Installation from Github and Development Information

* [Windows](docs/current/windows.md)
* [Linux](docs/current/linux.md)

## VS Code configuration files

There are several [configuration files](https://github.com/flamusdiu/xleapp-project) that I have been using for VS Code.

## Compile to executable

**NOTE:** This may not work at this time with this alpha version.

To compile to an executable so you can run this on a system without python installed.

To create xleapp.exe, run:

```bash
pyinstaller --onefile xleapp.spec
```

To create xleappGUI.exe, run:

```bash
pyinstaller --onefile --noconsole xleappGUI.spec
```

## Usage

### CLI

```bash
$ xleapp -h
usage: xleapp [-h] [-I] [-R] [-A] [-C] [-V] [-o OUTPUT_FOLDER] [-i INPUT_PATH]
       [--artifacts [ARTIFACTS ...]] [-p] [-l] [--gui] [--version]

xLEAPP: Logs, Events, and Plists Parser.

optional arguments:
  -h, --help            show this help message and exit
  -I                    parse ios artifacts
  -R                    parse Warrant Returns / User Generated Archives artifacts
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

```bash
$ xleapp --gui

```

### Help

```bash
$ xleapp.py --help

```

The GUI will open in another window.

## Acknowledgements

This tool is the result of a collaborative effort of many people in the DFIR community.

This product includes software developed by Sarah Edwards (Station X Labs, LLC, @iamevltwin, mac4n6.com) and other contributors as part of APOLLO (Apple Pattern of Life Lazy Output'er).
