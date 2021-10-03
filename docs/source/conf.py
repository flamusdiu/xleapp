import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join('..', '..')))

import sphinx_rtd_theme

project = 'xLEAPP'
copyright = '2021, Alexis Brignoni'
author = 'Alexis Brignoni'
release = '0.0.1'

extensions = [
    "recommonmark",
    "sphinx_rtd_theme",
    "sphinxcontrib.images",
    "sphinxcontrib.napoleon",
    "sphinxcontrib.mermaid",
    "sphinx.ext.autodoc",
    "autoapi.extension",
]

templates_path = ['_templates']
exclude_patterns = []
source_suffix = '.rst'
master_doc = 'index'

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:
    html_theme = 'sphinx_rtd_theme'

html_static_path = ['_static']

# autoapi configuration
autoapi_type = 'python'
autoapi_dirs = ['../../src/xleapp']
autoapi_add_toctree_entry = False
# Options: https://sphinx-autoapi.readthedocs.io/en/latest/reference/config.html#customisation-options
autoapi_options = [
    'members',
    'inherited-members',
    'private-members',
    'special-members',
    'show-inheritance',
]
autodoc_typehints = 'description'
autoapi_python_class_content = 'both'
autoapi_root = 'api'

html_use_smartypants = True
html_last_updated_fmt = '%b %d, %Y'
html_split_index = False

napoleon_use_ivar = True
napoleon_use_rtype = False
napoleon_use_param = False

images_config = {'default_image_width': "50%", 'default_image_height': "50%"}
