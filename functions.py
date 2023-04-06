from math import ceil
import aiohttp


UNITS = ["", "K", "M", "G", "T", "P", "E", "Z"]


def format_size(number: int, suffix: str = "B") -> str:
    """
    Return file size in human readable format.
    """
    for unit in UNITS:
        if abs(number) < 1024.0:
            return f"{number:.1f} {unit}{suffix}"
        number /= 1024.0
    return f"{number:.1f} Y{suffix}"


async def get_headers(url: str) -> dict:
    """
    Send head request to the specified url and return the headers.
    """
    async with aiohttp.ClientSession() as session:
        async with session.head(url, allow_redirects=True) as response:
            return dict(response.headers)


def calc_file_chunks(
    file_size: int,
    min_chunk_size: int = None,
    max_chunk_size: int = None,
) -> tuple:
    """
    Calculate the file chunks based on the min and max chunk size.
    """
    if min_chunk_size is None:
        min_chunk_size = 10 * 1024 * 1024
    if max_chunk_size is None:
        max_chunk_size = 100 * 1024 * 1024
    total_parts = 3
    while (
        ceil(file_size / total_parts) < min_chunk_size
        and total_parts > 1
    ):
        total_parts -= 1
    while (
        ceil(file_size / total_parts) > max_chunk_size
        and total_parts < 6
    ):
        total_parts += 1
    if total_parts < 1:
        total_parts = 1
    chunk = ceil(file_size / total_parts)
    splitted_parts = []
    for part in range(total_parts):
        from_byte = part * chunk
        to_byte = (from_byte + chunk) - 1
        if to_byte > file_size:
            to_byte = file_size
        splitted_parts.append((from_byte, to_byte))
    verify_splitted_chunks(splitted_parts, file_size)
    return splitted_parts, chunk


def verify_splitted_chunks(parts: list, file_size: int) -> bool:
    """
    Verify that the sum of calculated chunks is equal to the file size.
    """
    calc_size = sum(
        map(
            lambda part: part[1] - part[0] + 1,
            parts
        )
    )
    assert calc_size == file_size, "File size mismatch!"
