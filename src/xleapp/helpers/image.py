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
    imDirectory: Path,
    imFilename: str,
    seeker: FileSeekerBase,
    report_folder: Path,
) -> str:
    """
    searching for thumbnails, copy it to report folder and return tag  to
    insert in html
    """
    thumb = f"{g.app.default_configs.get('thumbnail_root')}/{imDirectory}/{imFilename}"
    thumblist = seeker.search(f"{thumb}/**.JPG", return_on_first_hit=True)
    thumbname = imDirectory.replace("/", "_") + "_" + imFilename + ".JPG"
    pathToThumb = os.path.join(
        os.path.basename(os.path.abspath(report_folder)),
        thumbname,
    )
    htmlThumbTag = '<img src="{0}"></img>'.format(pathToThumb)
    if thumblist:
        shutil.copyfile(thumblist[0], os.path.join(report_folder, thumbname))
    else:
        # recreate thumbnail from image
        # TODO: handle videos and HEIC
        files = seeker.search(
            f"{g.app.default_configs.get('MEDIA_ROOT')}/{imDirectory}/{imFilename}",
            return_on_first_hit=True,
        )
        if files:
            try:
                im = Image.open(files[0])
                im.thumbnail(g.app.default_configs.get("THUMB_SIZE"))
                im.save(os.path.join(report_folder, thumbname))
            except:  # noqa
                pass  # unsupported format
    return htmlThumbTag
