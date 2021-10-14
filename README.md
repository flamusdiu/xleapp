# xLEAPP

Framework for Logs, Events, And Plists Parser (LEAPP)

This framework is a complete rewrite of the excellent tool iLEAPP.Details of iLEAPP can be found in this [blog post](https://abrignoni.blogspot.com/2019/12/xleapp-ios-logs-events-and-properties.html)

xLEAPP is the framework created to merge several tools together. More information about the rewrite is given in by talk ([YouTube](https://www.youtube.com/watch?v=seTpCmSF0Gc)) at Black Hills Info Security's Wild West Hackin' Fest (WWHF): Deadwood in 2021.

## Features

* Provides a centralized and modular framework
* Provides a simplified way to write plugins (artifacts) for each different supported platform.
* Parses iOS, macOS, Android, Chromebook, warranty returns, and Windows artifacts depending on the plugins installed.

## Other Documentation

* [Artifact Creation](docs/current/artifact-creation.md)

## Pre-requisites

This project requires you to have Python >= 3.9

## Pre-requisites for Development

* make

  * Make provides a way to add extra commands to help with development of all plugins. The steps below only need to be completed once.
  * Windows: [ezwinports: make-4.3](https://sourceforge.net/projects/ezwinports/files/make-4.3-with-guile-w32-bin.zip/download)
    * Unzip to a folder of your choosing. Default is `C:\Windows\GnuWin32\bin`
    * The do the following to add to your path:

        1. On the Start menu, right-click Computer (Windows 10: This PC).
        2. On the context menu, click Properties.
        3. (Windows 10): On the About page under Related settings, click Advance system settings
        4. (Windows 7): In the System dialog box, click Advanced system settings.
        5. On the Advanced tab of the System Properties dialog box, click Environment Variables.
        6. In the System Variables box of the Environment Variables dialog box, scroll to Path and select it.
        7. Click the lower of the two Edit buttons in the dialog box.
        8. In the Edit System Variable dialog box, scroll to the end of the string in the Variable value box and add a semicolon (;).
        9. Add the new path after the semicolon. `C:\Windows\GnuWin32\bin`
        10. Click OK in three successive dialog boxes, and then close the System dialog box.

    > You might need to re-log into the computer to see system changes.

      Open a Powershell/CMD prompt, type `make -v` to see if works.

  * Linux:
    * Ubuntu/Debian: `apt install make`
    * RedHat/Fedora: `yum install make`
* git
  * [Getting Started - Installing Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

## Installation for development

### Folder Structure

If you follow all the information, you should end up with the following folders.

```txt
--| xleapp
    --| docs
    --| plugins
       --| xleapp-ios
       --| xleapp-ios-non-free
       --| <other plugins>
    --| src
```

### Windows (Powershell): Setup and Installation

Insure you have the requirements above before continuing.

```powershell
# Clone this repo
PS> git clone https://github.com/flamusdiu/xleapp.git
Cloning into 'xleapp'...
remote: Enumerating objects: 4869, done.
remote: Counting objects: 100% (4869/4869), done.
remote: Compressing objects: 100% (1387/1387), done.
remote: Total 4869 (delta 3444), reused 4830 (delta 3406), pack-reused 0
Receiving objects: 100% (4869/4869), 7.20 MiB | 11.94 MiB/s, done.
Resolving deltas: 100% (3444/3444), done.

# Install any plugins. These are specified with out the "xleapp-" prefix. 
PS> make DL_PLUGINS="ios" pkg-plugins
New-Item -Force -ItemType directory -Path plugins | Out-Null
pushd plugins && 'ios ios-non-free'.split(' ') | foreach {git clone https://github.com/flamusdiu/xleapp-$_.git} && popd
Cloning into 'xleapp-ios'...
remote: Enumerating objects: 257, done.
remote: Counting objects: 100% (257/257), done.
remote: Compressing objects: 100% (92/92), done.
remote: Total 257 (delta 159), reused 253 (delta 155), pack-reused 0 eceiving objects:  92% (237/257)
Receiving objects: 100% (257/257), 146.19 KiB | 1.35 MiB/s, done.
Resolving deltas: 100% (159/159), done.

PS> make install-poetry
poetry install
Updating dependencies
Resolving dependencies...

Writing lock file

Package operations: 64 installs, 0 updates, 0 removals

  • Installing smmap (4.0.0)
  • Installing gitdb (4.0.7)
  • Installing mccabe (0.6.1)
  • Installing pbr (5.6.0)

  <output snipped>

Installing the current project: xleapp (0.1.0)
pushd plugins && 'xleapp-ios'.split(' ') | foreach {pushd $_ && poetry install && popd} && popd
Creating virtualenv xleapp-ios-9uAnBasO-py3.9 in C:\Users\jesse\AppData\Local\pypoetry\Cache\virtualenvs
Updating dependencies
Resolving dependencies...

Writing lock file

Package operations: 16 installs, 0 updates, 0 removals

  • Installing six (1.16.0)
  • Installing soupsieve (2.2.1)
  • Installing beautifulsoup4 (4.10.0)

  <output snipped>
Installing the current project: xleapp-ios (0.1.0)
```

## VS Code configuration files

There are several configuration files that I have been using for VS Code. You can find those here: https://github.com/flamusdiu/xleapp-project


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
usage: xleapp [-h] [-I] [-R] [-A] [-C] [-V] [-o OUTPUT_FOLDER] [-i INPUT_PATH] [--artifact [ARTIFACT ...]]
              [-p] [-l] [--gui] [--version]

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
