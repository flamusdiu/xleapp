from . import application
from . import archive
from . import audio
from . import document
from . import font
from . import image
from . import text
from . import video
from .base import MagicType


# Supported image types
IMAGE: list[MagicType] = [
    image.Dwg(),
    image.Xcf(),
    image.Jpeg(),
    image.Jpx(),
    image.Apng(),
    image.Png(),
    image.Gif(),
    image.Webp(),
    image.Tiff(),
    image.Cr2(),
    image.Bmp(),
    image.Jxr(),
    image.Psd(),
    image.Ico(),
    image.Heic(),
    image.Dcm(),
    image.Avif(),
    image.Qoi(),
]

# Supported video types
VIDEO: list[MagicType] = [
    video.M3gp(),
    video.Mp4(),
    video.M4v(),
    video.Mkv(),
    video.Mov(),
    video.Avi(),
    video.Wmv(),
    video.Mpeg(),
    video.Webm(),
    video.Flv(),
]

# Supported audio types
AUDIO: list[MagicType] = [
    audio.Aac(),
    audio.Midi(),
    audio.Mp3(),
    audio.M4a(),
    audio.Ogg(),
    audio.Flac(),
    audio.Wav(),
    audio.Amr(),
    audio.Aiff(),
]

# Supported font types
FONT: list[MagicType] = [font.Woff(), font.Woff2(), font.Ttf(), font.Otf()]

# Supported archive container types
ARCHIVE: list[MagicType] = [
    archive.Br(),
    archive.Rpm(),
    archive.Dcm(),
    archive.Epub(),
    archive.Zip(),
    archive.Tar(),
    archive.Rar(),
    archive.Gz(),
    archive.Bz2(),
    archive.SevenZ(),
    archive.Pdf(),
    archive.Exe(),
    archive.Swf(),
    archive.Rtf(),
    archive.Nes(),
    archive.Crx(),
    archive.Cab(),
    archive.Eot(),
    archive.Ps(),
    archive.Xz(),
    archive.Sqlite(),
    archive.Deb(),
    archive.Ar(),
    archive.Z(),
    archive.Lzop(),
    archive.Lz(),
    archive.Elf(),
    archive.Lz4(),
    archive.Zstd(),
]

# Supported archive container types
APPLICATION: list[MagicType] = [
    application.Wasm(),
]

# Supported document types
DOCUMENT: list[MagicType] = [
    document.Doc(),
    document.Docx(),
    document.Odt(),
    document.Xls(),
    document.Xlsx(),
    document.Ods(),
    document.Ppt(),
    document.Pptx(),
    document.Odp(),
]

# Supported text types
TEXT: list[MagicType] = [
    text.Json(),
    text.Plist(),
    text.Html(),
]


# Expose supported type matchers
MAGIC_TYPES: list[MagicType] = (
    IMAGE + AUDIO + VIDEO + FONT + DOCUMENT + ARCHIVE + APPLICATION + TEXT
)
