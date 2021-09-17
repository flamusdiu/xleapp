import shutil
import os
import ileapp.ilapglobals as g
import sqlite3
import simplekml
from PIL import Image


def generate_thumbnail(imDirectory, imFilename, seeker, report_folder):
    '''
    searching for thumbnails, copy it to report folder and return tag  to
    insert in html
    '''
    thumb = f'{g.thumbnail_root}/{imDirectory}/{imFilename}'
    thumblist = seeker.search(f'{thumb}/**.JPG', return_on_first_hit=True)
    thumbname = imDirectory.replace('/', '_') + '_' + imFilename + '.JPG'
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
            f'{g.media_root}/{imDirectory}/{imFilename}', return_on_first_hit=True
        )
        if files:
            try:
                im = Image.open(files[0])
                im.thumbnail(g.thumb_size)
                im.save(os.path.join(report_folder, thumbname))
            except:  # noqa
                pass  # unsupported format
    return htmlThumbTag


def kmlgen(report_folder, kmlactivity, data_list, data_headers):
    report_folder = report_folder.rstrip('/')
    report_folder = report_folder.rstrip('\\')
    report_folder_base, tail = os.path.split(report_folder)
    kml_report_folder = os.path.join(report_folder_base, '_KML Exports')
    if os.path.isdir(kml_report_folder):
        latlongdb = os.path.join(kml_report_folder, '_latlong.db')
        db = sqlite3.connect(latlongdb)
        cursor = db.cursor()
        cursor.execute('''PRAGMA synchronous = EXTRA''')
        cursor.execute('''PRAGMA journal_mode = WAL''')
        db.commit()
    else:
        os.makedirs(kml_report_folder)
        latlongdb = os.path.join(kml_report_folder, '_latlong.db')
        db = sqlite3.connect(latlongdb)
        cursor = db.cursor()
        cursor.execute(
            """
            CREATE TABLE data(key TEXT, latitude TEXT,
            longitude TEXT, activity TEXT)
            """
        )
        db.commit()

    kml = simplekml.Kml(open=1)

    a = 0
    length = len(data_list)
    while a < length:
        modifiedDict = dict(zip(data_headers, data_list[a]))
        times = modifiedDict['Timestamp']
        lon = modifiedDict['Longitude']
        lat = modifiedDict['Latitude']
        if lat:
            pnt = kml.newpoint()
            pnt.name = times
            pnt.description = f"Timestamp: {times} - {kmlactivity}"
            pnt.coords = [(lon, lat)]
            cursor.execute(
                "INSERT INTO data VALUES(?,?,?,?)", (times, lat, lon, kmlactivity)
            )
        a += 1
    db.commit()
    db.close()
    kml.save(os.path.join(kml_report_folder, f'{kmlactivity}.kml'))
