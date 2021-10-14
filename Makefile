ifeq ($(OS),Windows_NT)
# Uses Powershell to run make instead of cmd
SHELL := pwsh.exe
.SHELLFLAGS := -Command
endif

SOURCEDIR = src/xleapp
PLUGINDIR = plugins
BASEREPO = https://github.com/flamusdiu

PLUGINS := '$(shell $$(Get-ChildItem -Directory $(PLUGINDIR)).name)'.split(' ')
VENV = .venv/bin/activate.ps1

install:
	python -m venv .venv
	$(VENV) && pip install -r requirements-dev.txt

install-poetry:
	poetry install
	pushd $(PLUGINDIR) && $(PLUGINS)| foreach {pushd $$_ && poetry install && popd} && popd
# Need to install the plugins in the make application folder. This created dev_depends. However,
# this are not saved in poetry file at the time.
	$(PLUGINS) | foreach {poetry add -D $(PLUGINDIR)/$$_}

pkg-update:
	poetry update
	pushd $(PLUGINDIR) && $(PLUGINS) | foreach {pushd $$_ && poetry update && popd} && popd

pkg-gen-requirements:
# we have todo without hashes due to https://github.com/pypa/pip/issues/4995
	poetry export --dev --without-hashes -f requirements.txt > requirements.txt
	for pkg in $(PLUGINS); do pushd $$pkg && poetry export --without-hashes -f requirements.txt > requirements.txt && popd; done

pkg-plugins:
# Use to download plugins
# make DL_PLUGINS="ios ios-non-free" pkg-plugins
	New-Item -Force -ItemType directory -Path $(PLUGINDIR) | Out-Null
	pushd $(PLUGINDIR) && '$(DL_PLUGINS)'.split(' ') | foreach {git clone $(BASEREPO)/xleapp-$$_.git} && popd

pkg-check-plugins:
	 python -c "exec(""""try: from importlib.metadata import entry_points; plugins=[plugin for plugin in entry_points()['xleapp.plugins']]; [print(p) for p in {plugin.value.split(':')[0] for plugin in plugins}];\nexcept KeyError: print('No plugins found! Are you in a poetry virtual enviroment (hint: `poetry shell`)?');"""")"