ifeq ($(OS),Windows_NT)
    # Uses Powershell to run make instead of cmd
    SHELL := pwsh.exe
    .SHELLFLAGS := -Command
    VENV := .venv/Scripts/Activate.ps1
else
    VENV := .venv/bin/activate
endif

PYPIREPO := pypi
SOURCEDIR := src/xleapp
PLUGINDIR := plugins
BASEREPO := https://github.com/flamusdiu

space := $(subst ,, )
comma := ,

PLUGINS :=  '$(shell $$(Get-ChildItem -Directory $(PLUGINDIR)).name)'

ifdef DL_PLUGINS
	GIT_PLUGINS := @('$(DL_PLUGINS)'.split(' '))
else
	GIT_PLUGINS := 'extensions', 'extensions-non-free'
endif

# Function to wrap calls needing to run in each plugin directory
define plugin_run
@$&(pushd $(PLUGINDIR) && $(PLUGINS) | foreach {pushd $$_ && $(1) && popd} && popd)
endef

install: pkg-update
	@poetry install -E lint -E tests -E docs -E vscode
	$(call plugin_run, poetry install)
# Need to install the plugins in the make application folder. This created dev_depends.
# However, these are not saved in poetry file at the time.
	$(PLUGINS) | foreach {pip install -e $(PLUGINDIR)/$$_}

pkg-update:
	@poetry update
	$(call plugin_run, poetry update)

pkg-show-update:
	@poetry show -o
	$(call plugin_run, poetry show -o)

pkg-requirements:
# we have todo without hashes due to https://github.com/pypa/pip/issues/4995
	poetry export --dev --without-hashes -f requirements.txt > requirements.txt
	$(call plugin_run,poetry export --without-hashes -f requirements.txt > requirements.txt)

pkg-freeze-setup:
	python tools/dev/poetrypkg.py gen-frozensetup -p .
	$(call plugin_run, python tools/dev/poetrypkg.py gen-frozensetup -p $$_)

pkg-increment:
	@echo "Bumping version of xLEAPP..."
	@poetry version prerelease

pkg-plugin-increment:
	$(call plugin_run,Write-Host "Bumping version of $$_ ..." && poetry version prerelease)

pkg-publish-wheel:
# clean up any artifacts first
	rm -r -Force dist/*
# generate setup
	poetry build
# check wheel
	twine check dist/*
# upload to test pypi
	twine upload -r $(PYPIREPO) dist/*

pkg-plugins-publish-wheel:
# clean up any artifacts first
	$(call plugin_run, rm -Force dist/*)
# generate setup
	$(call plugin_run, poetry build)
# check wheel
	$(call plugin_run,twine check dist/*)
# upload to test pypi
	$(call plugin_run,twine upload -r $(PYPIREPO) dist/*)

clean:
	rm -r -Force dist/*
	$(call plugin_run, rm -Force dist/*)
# Removes plugins from pyproject.toml file. These should not be commited this way.
	@echo "Removing plugins from pyproject.toml file!"
	poetry update

pkg-plugins:
#Use to download plugins
# make DL_PLUGINS="ios ios-non-free" pkg-plugins

	@New-Item -Force -ItemType directory -Path $(PLUGINDIR) | Out-Null
	@echo $(GIT_PLUGINS)
	$(GIT_PLUGINS) | foreach{git clone $(BASEREPO)/xleapp-$$_.git ${PLUGINDIR}/xleapp-$$_}

pkg-check-plugins:
	@echo "Checking for installed plugins ..."
	@poetry run python -c "exec(""""try: from importlib.metadata import entry_points; plugins=[plugin for plugin in entry_points()['xleapp.plugins']]; [print(f'    -> {p}') for p in {plugin.value.split(':')[0] for plugin in plugins}];\nexcept KeyError: print('No plugins found!');"""")"
