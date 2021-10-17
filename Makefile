ifeq ($(OS),Windows_NT)
# Uses Powershell to run make instead of cmd
SHELL := pwsh.exe
.SHELLFLAGS := -Command
endif

PYPIREPO := testpypi
SOURCEDIR := src/xleapp
PLUGINDIR := plugins
BASEREPO := https://github.com/flamusdiu

space := $(subst ,, )
comma := ,

PLUGINS :=  '$(shell $$(Get-ChildItem -Directory $(PLUGINDIR)).name)'

VENV := .venv/bin/activate.ps1

ifdef DL_PLUGINS
	GIT_PLUGINS := @('$(DL_PLUGINS)'.split(' '))
else
	GIT_PLUGINS := 'ios', 'ios-non-free'
endif

# Function to wrap calls needing to run in each plugin directory
define plugin_run
@$&(pushd $(PLUGINDIR) && $(PLUGINS) | foreach {pushd $$_ && $(1) && popd} && popd)
endef

install:
	@python -m venv .venv
	@$(VENV) && pip install -r requirements-dev.txt

install-poetry: pkg-update
	@poetry install
	$(call plugin_run, poetry install)
# Need to install the plugins in the make application folder. This created dev_depends. However,
# this are not saved in poetry file at the time.
	$(PLUGINS) | foreach {poetry add -D $(PLUGINDIR)/$$_}

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
	$(call plugin_run,Write-Host "Bumping version of $$_ ..." && poetry version prerelease)

pkg-publish-wheel:
# clean up any artifacts first
	rm -r -Force dist/*
	$(call plugin_run, rm -Force dist/*)
# increment versions

# generate setup
	poetry build
	$(call plugin_run, poetry build)
# check wheel
	twine check dist/*
	$(call plugin_run,twine check dist/*)
# upload to test pypi
	twine upload -r testpypi dist/*
	$(call plugin_run,twine upload -r testpypi dist/*)

clean:
	rm -r -Force dist/*
	$(call plugin_run, rm -Force dist/*)
# Removes plugins from pyproject.toml file. These should not be commited this way.
	@echo "Removing plugins from pyproject.toml file!"
	@&(Set-Content -Path .\pyproject.toml -Value (Get-Content .\pyproject.toml | Select-String -Pattern "xleapp-[\w-]+\s?=\s?" -NotMatch))
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