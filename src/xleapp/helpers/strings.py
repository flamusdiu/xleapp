def raw(data) -> str:
    """Returns string of printable characters. Replacing non-printable characters
    with '.', or CHR(46)
    ``"""
    return "".join(
        [chr(byte) if byte >= 0x20 and byte < 0x7F else chr(46) for byte in data]
    )


def print(data) -> str:
    """Returns string of printable characters. Works similar to the Linux
    `string` function.
    """
    cleansed = "".join(
        [chr(byte) if byte >= 0x20 and byte < 0x7F else chr(0) for byte in data]
    )
    return filter(lambda string: len(string) >= 4, cleansed.split(chr(0)))
