from typing import Union


def chr_py3(num: int) -> bytes:
    if not isinstance(num, bytes):
        return bytes([num])
    else:
        return num


def ord_py3(num: bytes) -> Union[int, bytes]:
    if isinstance(num, bytes) or isinstance(num, str):
        return ord(num)
    else:
        return num


def str_to_bytes(text):
    if isinstance(text, str):
        return text.encode('latin-1')
    else:
        return text


def bytes_to_str(text):
    if not isinstance(text, str):
        return text.decode('latin-1')
    else:
        return text
