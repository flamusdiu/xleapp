import os
import shutil

from PIL import Image

import xleapp.globals as g


def generate_thumbnail(imDirectory, imFilename, seeker, report_folder):
    """
    searching for thumbnails, copy it to report folder and return tag  to
    insert in html
    """
    thumb = f"{g.thumbnail_root}/{imDirectory}/{imFilename}"
    thumblist = seeker.search(f"{thumb}/**.JPG", return_on_first_hit=True)
    thumbname = imDirectory.replace("/", "_") + "_" + imFilename + ".JPG"
    pathToThumb = os.path.join(
        os.path.basename(os.path.abspath(report_folder)), thumbname
    )
    htmlThumbTag = '<img src="{0}"></img>'.format(pathToThumb)
    if thumblist:
        shutil.copyfile(thumblist[0], os.path.join(report_folder, thumbname))
    else:
        # recreate thumbnail from image
        # TODO: handle videos and HEIC
        files = seeker.search(
            f"{g.media_root}/{imDirectory}/{imFilename}", return_on_first_hit=True
        )
        if files:
            try:
                im = Image.open(files[0])
                im.thumbnail(g.thumb_size)
                im.save(os.path.join(report_folder, thumbname))
            except:  # noqa
                pass  # unsupported format
    return htmlThumbTag
