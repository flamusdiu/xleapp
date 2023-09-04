#!/bin/sh

packages="poetry pre-commit tox isort ruff pyright"

types_inject="types-PyYAML types-Jinja2 types-pillow"

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
