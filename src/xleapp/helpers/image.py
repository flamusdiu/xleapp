import os
import shutil
import typing as t

from pathlib import Path

from PIL import (  # type: ignore  # https://github.com/python-pillow/Pillow/issues/2625
    Image,
)

import xleapp.globals as g


if t.TYPE_CHECKING:
    from xleapp.helpers.search import FileSeekerBase


def generate_thumbnail(
    image_directory: Path,
    image_filename: str,
    seeker: FileSeekerBase,
    report_folder: Path,
) -> str:
    """
    searching for thumbnails, copy it to report folder and return tag  to
    insert in html
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
    html_thumb_tag = '<img src="{0}"></img>'.format(path_to_thumb)
    if thumb_list:
        shutil.copyfile(thumb_list[0], os.path.join(report_folder, thumb_name))
    else:
        # recreate thumbnail from image
        # TODO: handle videos and HEIC
        files = seeker.search(
            f"{g.app.default_configs.get('MEDIA_ROOT')}/{image_directory}/{image_filename}",
        )
        if files:
            try:
                im = Image.open(files[0])
                im.thumbnail(g.app.default_configs.get("THUMB_SIZE"))
                im.save(os.path.join(report_folder, thumb_name))
            except:  # noqa
                pass  # unsupported format
    return html_thumb_tag
