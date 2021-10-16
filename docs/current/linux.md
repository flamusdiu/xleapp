# Linux

* [Installation From Github](#installation-from-github)
* [Installation for development](#installation-for-deployment)
  * [Pre-requisites for Development](#pre-requisites-for-development)
  * [Folder Structure](#folder-structure)
  * [Setup and Installation](#setup-installation)

<h2 id="installation-from-githu">Installation from Github (Bash/Python)</h2>

```bash
# Install pipx
# See Linux: https://github.com/pypa/pipx#on-linux-install-via-pip-requires-pip-190-or-later
$ python3 -m pip install --user pipx
$ python3 -m pipx ensurepath
```

```bash
# Clone this repo. Current working branch.
$ git clone https://github.com/flamusdiu/xleapp.git
Cloning into "xleapp"...
remote: Enumerating objects: 4869, done.
remote: Counting objects: 100% (4869/4869), done.
remote: Compressing objects: 100% (1387/1387), done.
remote: Total 4869 (delta 3444), reused 4830 (delta 3406), pack-reused 0
Receiving objects: 100% (4869/4869), 7.20 MiB | 10.35 MiB/s, done.
Resolving deltas: 100% (3444/3444), done.

# Change directory to "xleapp"
$ cd xleapp

# Install using pipx
$ pipx install .
```

<h2 id="installation-for-development">Installation for development</h2>

<h3 id="pre-requisites-for-development">Pre-requisites for Development</h3>

* [poetry](https://python-poetry.org/)
  * Download and install ([docs](https://python-poetry.org/docs/#installation)):

    ```bash
    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
    ```

* make
  * Ubuntu/Debian: `apt install make`
  * RedHat/Fedora: `yum install make`
* git
  * [Getting Started - Installing Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
  * Ubuntu/Debian: `apt install git`
  * RedHat/Fedora: `yum install git`


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

```bash
# Clone this repo
$ git clone https://github.com/flamusdiu/xleapp.git
Cloning into "xleapp"...
remote: Enumerating objects: 4869, done.
remote: Counting objects: 100% (4869/4869), done.
remote: Compressing objects: 100% (1387/1387), done.
remote: Total 4869 (delta 3444), reused 4830 (delta 3406), pack-reused 0
Receiving objects: 100% (4869/4869), 7.20 MiB | 11.94 MiB/s, done.
Resolving deltas: 100% (3444/3444), done.

# Install any plugins. These are specified with out the "xleapp-" prefix. 
$ make DL_PLUGINS="ios" pkg-plugins
Cloning into "xleapp-ios"...
remote: Enumerating objects: 257, done.
remote: Counting objects: 100% (257/257), done.
remote: Compressing objects: 100% (92/92), done.
remote: Total 257 (delta 159), reused 253 (delta 155), pack-reused 0 
Receiving objects:  92% (237/257)
Receiving objects: 100% (257/257), 146.19 KiB | 1.35 MiB/s, done.
Resolving deltas: 100% (159/159), done.

$ make install-poetry
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
$ xleapp -h
usage: xleapp [-h] [-I] [-R] [-A] [-C] [-V] [-o OUTPUT_FOLDER] [-i INPUT_PATH] 
              [--artifact [ARTIFACT ...]] [-p] [-l] [--gui] [--version]
```
