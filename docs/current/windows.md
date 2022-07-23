# Windows

* [Installation From Github](#installation-from-github)
* [Installation for development](#installation-for-deployment)
  * [Pre-requisites for Development](#pre-requisites-for-development)
  * [Folder Structure](#folder-structure)
  * [Setup and Installation](#setup-installation)

<h2 id="installation-from-github">Installation from Github (Powershell/Python)</h2>

```powershell
# Install pipx
# Windows information: https://github.com/pypa/pipx#on-windows-install-via-pip-requires-pip-190-or-later
PS> python -m pip install --user pipx
```

It is possible (even most likely) the above finishes with a WARNING looking similar to this:

```powershell
WARNING: The script pipx.exe is installed in `<USER folder>\AppData\Roaming\Python\Python3x\Scripts` which is not on PATH
```

If so, go to the mentioned folder, allowing you to run the pipx executable directly. Enter the following line (even if you did not get the warning):

```powershell
PS> .\pipx ensurepath
```

This above did not work for me. I had to manually set the path:

* The do the following to add to your path:

  1. On the Start menu, right-click Computer (Windows 10: This PC).
  2. On the context menu, click Properties.
  3. (Windows 10): On the About page under Related settings, click Advance system settings
  4. (Windows 7): In the System dialog box, click Advanced system settings.
  5. On the Advanced tab of the System Properties dialog box, click Environment Variables.
  6. In the System Variables box of the Environment Variables dialog box, scroll to Path and select it.
  7. Click the lower of the two Edit buttons in the dialog box.
  8. In the Edit System Variable dialog box, scroll to the end of the string in the Variable value box and add a semicolon ( &#59; ).
  9. Add the new path after the semicolon. `C:\Tools\GnuWin32\bin`
  10. Click OK in three successive dialog boxes, and then close the System dialog box.

Then run the following to update your path without logging out:

```powershell
PS> $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```

```powershell
# Clone this repo. Current working branch.
PS> git clone https://github.com/flamusdiu/xleapp.git
Cloning into "xleapp"...
remote: Enumerating objects: 4869, done.
remote: Counting objects: 100% (4869/4869), done.
remote: Compressing objects: 100% (1387/1387), done.
remote: Total 4869 (delta 3444), reused 4830 (delta 3406), pack-reused 0
Receiving objects: 100% (4869/4869), 7.20 MiB | 10.35 MiB/s, done.
Resolving deltas: 100% (3444/3444), done.

# Change directory to "xleapp"
PS> cd xleapp

# Install using pipx
PS> pipx install .
```

<h2 id="installation-for-development">Installation for development</h2>

<h3 id="pre-requisites-for-development">Pre-requisites for Development</h3>

* [poetry](https://python-poetry.org/)
  * Download and install ([docs](https://python-poetry.org/docs/#installation)):

  ```powershell
  PS> (Invoke-WebRequest `
  -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py `
  -UseBasicParsing).Content | python -
  ```

* make

  * Make provides a way to add extra commands to help with development of all plugins. The steps below only need to be completed once.
  * Windows: [ezwinports: make-4.3](https://sourceforge.net/projects/ezwinports/files/make-4.3-with-guile-w32-bin.zip/download)
    * Unzip to a folder of your choosing. Default is `C:\Program Files (x86)\GnuWin32\bin`. **NOTE:** Do not use this path. The "(86)" in the path will cause problems with running make. Use something like `C:\Tools\GnuWin32\bin` instead.
    * The do the following to add to your path:

        1. On the Start menu, right-click Computer (Windows 10: This PC).
        2. On the context menu, click Properties.
        3. (Windows 10): On the About page under Related settings, click Advance system settings
        4. (Windows 7): In the System dialog box, click Advanced system settings.
        5. On the Advanced tab of the System Properties dialog box, click Environment Variables.
        6. In the System Variables box of the Environment Variables dialog box, scroll to Path and select it.
        7. Click the lower of the two Edit buttons in the dialog box.
        8. In the Edit System Variable dialog box, scroll to the end of the string in the Variable value box and add a semicolon ( &#59; ).
        9. Add the new path after the semicolon. `C:\Tools\GnuWin32\bin`
        10. Click OK in three successive dialog boxes, and then close the System dialog box.

      Then run the following to update your path without logging out:

      ```powershell
      PS> $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
      ```

    > You will need to run `make` with Powershell (`pwsh.exe`) since the commands are written in Powershell.

      Open a Powershell prompt, type `make -v` to see if works.
* git
  * [Getting Started - Installing Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

<h3 id="folder-structure">Folder Structure</h2>

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

<h3 id="setup-installation">Setup and Installation</h2>

Insure you have the requirements above before continuing.

```powershell
# Clone this repo
PS> git clone https://github.com/flamusdiu/xleapp.git
Cloning into "xleapp"...
remote: Enumerating objects: 4869, done.
remote: Counting objects: 100% (4869/4869), done.
remote: Compressing objects: 100% (1387/1387), done.
remote: Total 4869 (delta 3444), reused 4830 (delta 3406), pack-reused 0
Receiving objects: 100% (4869/4869), 7.20 MiB | 11.94 MiB/s, done.
Resolving deltas: 100% (3444/3444), done.

# Install any plugins. These are specified with out the "xleapp-" prefix.
PS> make DL_PLUGINS="ios" pkg-plugins
Cloning into "xleapp-ios"...
remote: Enumerating objects: 257, done.
remote: Counting objects: 100% (257/257), done.
remote: Compressing objects: 100% (92/92), done.
remote: Total 257 (delta 159), reused 253 (delta 155), pack-reused 0
Receiving objects:  92% (237/257)
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
Updating dependencies
Resolving dependencies...

Writing lock file

Package operations: 16 installs, 0 updates, 0 removals

  • Installing six (1.16.0)
  • Installing soupsieve (2.2.1)
  • Installing beautifulsoup4 (4.10.0)

  <output snipped>
Installing the current project: xleapp-ios (0.1.0)

# Test application
PS> xleapp -h
usage: xleapp [-h] [-I] [-R] [-A] [-C] [-V] [-o OUTPUT_FOLDER] [-i INPUT_PATH]
              [--artifact [ARTIFACT ...]] [-p] [-l] [--gui] [--version]
```
