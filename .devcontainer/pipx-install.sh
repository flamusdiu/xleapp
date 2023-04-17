#!/bin/sh

packages="poetry flakeheaven pre-commit tox isort pytest"

flakehaven_inject="flakeheaven flake8==4.0.1 flake8-bandit==3.0.0 flake8-bugbear==22.7.1 flake8-commas
flake8-comprehensions flake8-docstrings flake8-isort flake8-mutable flake8-quotes flake8-variables-names
flake8-builtins darglint flake8-eradicate pep8-naming==0.13.0 types-PyYAML types-Jinja2"

pytest_inject="pyfakefs pytest-cache pytest-cov pytest-dependency pytest-mock"

install() {
for p in $1; do
    pipx install $p;
done
}

inject() {
for p in $2; do
    pipx inject $1 $p;
done
}

install "${packages}"
inject flakeheaven "${flakehaven_inject}"
inject pytest "${pytest_inject}"

pip install --user tqdm requests pytest
