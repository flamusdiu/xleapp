import importlib
import inspect
import os
import pathlib
from collections import OrderedDict, namedtuple

from artifacts.lastBuild import LastBuild


def get_list_of_artifacts():
    """Generates a List of Artifacts installed

    Returns:
        dict: dictionary of artifacts with short names as keys
    """
    module_dir = pathlib.Path(importlib.util.find_spec(__name__).origin).parent
    artifact_list = OrderedDict()

    # Setup named tuple to hold each artifact
    Artifact = namedtuple('Artifact', ['name', 'cls'])
    Artifact.__doc__ += ': Loaded forensic artifact'
    Artifact.cls.__doc__ = 'Artifact object class'
    Artifact.name.__doc__ = 'Artifact short name'

    with os.scandir(module_dir) as it:
        for entry in it:
            if (entry.name.endswith(".py") and
                not (entry.name.startswith("__")
                     or entry.name.startswith('lastbuild'))):

                module_name = __name__ + '.' + entry.name[:-3]
                module = importlib.import_module(module_name)
                module_members = inspect.getmembers(module, inspect.isclass)

                for name, cls in module_members:
                    if (not str(cls.__module__).endswith('Artifact')
                            and str(cls.__module__).startswith(__name__)):
                        tmp_artifact = Artifact(name=cls().name, cls=cls())
                        artifact_list.update({name: tmp_artifact})

        # sort the artifact list
        tmp_artifact_list = sorted(list(artifact_list.items()))
        artifact_list.clear()
        artifact_list.update(tmp_artifact_list)

        # Create 'Last Build' artifact and move to top of the artifact list
        lastBuild = Artifact(name='Last Build', cls=LastBuild())
        artifact_list.update({'LastBuild': lastBuild})
        artifact_list.move_to_end('LastBuild', last=False)
    return artifact_list
