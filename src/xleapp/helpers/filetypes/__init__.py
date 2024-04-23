from . import application, archive, audio, document, font, image, text, video
from .base import MagicType

# Supported image types
IMAGE: list[MagicType] = [
    image.Apng(),
    image.Avif(),
    image.Bmp(),
    image.Cr2(),
    image.Dcm(),
    image.Dwg(),
    image.Gif(),
    image.Heic(),
    image.Ico(),
    image.Jpeg(),
    image.Jpx(),
    image.Jxr(),
    image.Png(),
    image.Psd(),
    image.Qoi(),
    image.Tiff(),
    image.Webp(),
    image.Xcf(),
]

# Supported video types
VIDEO: list[MagicType] = [
    video.Avi(),
    video.Flv(),
    video.M3gp(),
    video.M4v(),
    video.Mkv(),
    video.Mov(),
    video.Mp4(),
    video.Mpeg(),
    video.Webm(),
    video.Wmv(),
]

# Supported audio types
AUDIO: list[MagicType] = [
    audio.Aac(),
    audio.Aiff(),
    audio.Amr(),
    audio.Flac(),
    audio.M4a(),
    audio.Midi(),
    audio.Mp3(),
    audio.Ogg(),
    audio.Wav(),
]

# Supported font types
FONT: list[MagicType] = [
    font.Otf(),
    font.Ttf(),
    font.Woff(),
    font.Woff2(),
]

# Supported archive container types
ARCHIVE: list[MagicType] = [
    archive.Ar(),
    archive.Br(),
    archive.Bz2(),
    archive.Cab(),
    archive.Crx(),
    archive.Dcm(),
    archive.Deb(),
    archive.Elf(),
    archive.Eot(),
    archive.Epub(),
    archive.Exe(),
    archive.Gz(),
    archive.Lz(),
    archive.Lz4(),
    archive.Lzop(),
    archive.Nes(),
    archive.Pdf(),
    archive.Ps(),
    archive.Rar(),
    archive.Rpm(),
    archive.Rtf(),
    archive.SevenZ(),
    archive.Sqlite(),
    archive.Swf(),
    archive.Tar(),
    archive.Xz(),
    archive.Z(),
    archive.Zip(),
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


# Expose supported type matchers. Keep Order
MAGIC_TYPES: list[MagicType] = list(
    IMAGE + AUDIO + VIDEO + FONT + DOCUMENT + ARCHIVE + APPLICATION + TEXT
)
