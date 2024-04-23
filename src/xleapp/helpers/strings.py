def binary_sublength(array: bytes, char: int) -> int:
    if array.count(char) == 0:
        return 0
    num = first = array.index(char)
    second = 0

    while True:
        num += 1
        try:
            second = array.index(char, num)
        except ValueError:
            break
    return second - first + 1
