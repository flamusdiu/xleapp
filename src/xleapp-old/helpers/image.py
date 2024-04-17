import os
import pathlib
import shutil

import xleapp.globals as g

from PIL import Image
from xleapp.helpers.search import FileSeekerBase


def generate_thumbnail(
    image_directory: pathlib.Path,
    image_filename: str,
    seeker: FileSeekerBase,
    report_folder: pathlib.Path,
) -> str:
    """
    searching for thumbnails, copy it to report folder and return tag  to
    insert in htmli

    Args:
        image_directory (Path): path to the image
        image_filename (str): file name of the image
        seeker (FileSeekerBase): :obj:`FileSeekerBase` to find the image
        report_folder (Path): location to save the file

    Returns:
        str: string of the html tag for the thumbnail
    """
    thumb = f"{g.app.default_configs.get('thumbnail_root')}/{image_directory}/{image_filename}"
    thumb_list = seeker.search(f"{thumb}/**.JPG", return_on_first_hit=True)
    thumb_name = (
        f"{str(image_directory.resolve()).replace('/', '_')}_{image_filename}.JPG"
    )
    path_to_thumb = os.path.join(
        os.path.basename(os.path.abspath(report_folder)),
        thumb_name,
    )
    html_thumb_tag = f'<img src="{path_to_thumb}"></img>'
    if thumb_list:
        shutil.copyfile(thumb_list[0], os.path.join(report_folder, thumb_name))
    else:
        # recreate thumbnail from image
        # TODO: handle videos and HEIC
        files = seeker.search(
            f"{g.app.default_configs.get('MEDIA_ROOT')}/{image_directory}/{image_filename}",
        )
        if files:
            im = Image.open(files[0])
            im.thumbnail(g.app.default_configs.get("THUMB_SIZE"))
            im.save(os.path.join(report_folder, thumb_name))
    return html_thumb_tag
