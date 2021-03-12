from setuptools import setup, find_packages
import pathlib


def read(rel_path):
    here = pathlib.Path('.').parent.resolve()
    return (here / rel_path).read_text()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            # __version__ = "0.9"
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")


long_description = read('README.md')

setup(
    name='iLEAPP',
    version=get_version("ileapp/__init__.py"),
    description="iOS Logs, Events, And Plists Parser",
    long_description=long_description,
    license='MIT',
    classifiers=[

    ],
    url='https://github.com/abrignoni/iLEAPP',
    keywords='',
    project_urls={
        "Documentation": "https://github.com/abrignoni/iLEAPP/wiki",
        "Source": "https://github.com/abrignoni/iLEAPP"
    },
    author='Alexis Brignoni, Yogesh Khatri',
    package_dir={"": "ileapp"},
    packages=find_packages(
        where="ileapp",
        exclude=["contrib", "docs", "tests*", "tasks"]
    ),
    entry_points={
        "console_scripts": {
            "ileap=ileapp.__main__:cli"
        },
    },
    zip_safe=True,
    python_requires='>=3.6'
)
