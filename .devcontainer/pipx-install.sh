#!/bin/sh

packages="poetry pre-commit tox isort sphinx ruff pyright"

types_inject="types-PyYAML types-Jinja2 types-pillow"
pytest_inject="pyfakefs pytest-cache pytest-cov pytest-dependency pytest-mock tqdm requests"
sphinx_inject="sphinx-rtd-theme sphinxcontrib-images sphinxcontrib-mermaid sphinxcontrib-napoleon"

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
inject ruff "${types_inject}"
inject pytest "${pytest_inject}"
inject sphinx "${sphinx_inject}"

pip install --user sphinx-rtd-theme docutils
