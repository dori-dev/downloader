import os
import datetime
from math import ceil
import asyncio
import aiohttp
import aiofiles
from aiofiles.os import remove as async_remove


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


async def download_part(
    url: str,
    temp_dir: str,
    file_name: str,
    queue: asyncio.Queue[int],
    id: int,
    from_byte: int,
    to_byte: int,
) -> tuple:
    """
    Download a specific part of the given file.
    """
    headers = {
        "Range": f"bytes={from_byte}-{to_byte}"
    }
    timeout = aiohttp.ClientTimeout(connect=8 * 60)
    async with aiohttp.ClientSession(
        headers=headers,
        timeout=timeout,
    ) as session:
        async with session.get(url) as response:
            file_path = os.path.join(temp_dir, f"{file_name}.part{id}")
            async with aiofiles.open(file_path, 'wb') as file:
                while True:
                    chunk = await response.content.read(10 * 1024 * 1024)
                    if not chunk:
                        break
                    await file.write(chunk)
                    await queue.put(len(chunk))
    await queue.put(-1)


async def show_progress(
    queue: asyncio.Queue[int],
    total_size: int,
    total_parts: int,
) -> None:
    """
    Show the progress of downloading the file.
    """
    downloaded = 0
    download_per_second = 0
    finished = 0
    while finished != total_parts:
        download_per_second = 0
        while not queue.empty():
            chunk_size = await queue.get()
            if chunk_size == -1:
                finished += 1
            download_per_second += chunk_size
        downloaded += download_per_second
        if download_per_second > 0:
            complete_count = ceil(downloaded / total_size * 50)
            remaining_seconds = (
                total_size / downloaded
            ) // download_per_second
            # display
            percent = ceil(downloaded / total_size * 100)
            completed = "=" * complete_count
            remaining = "-" * (50 - complete_count)
            remaining_time = datetime.timedelta(seconds=remaining_seconds)
            display = (
                f"{format_size(downloaded):10s} ({percent}%) "
                f"{completed}{remaining} "
                f"{format_size(download_per_second)}/s {remaining_time}"
            )
            end = "\r" if finished != total_parts else "\n"
            print(display, end=end)
        await asyncio.sleep(1)


async def merge_file_parts(
    file_name: str,
    temp_dir: str,
    total_parts: int,
) -> bool:
    """
    Merge the given file parts into a single file.
    """
    ids = list(range(1, total_parts + 1))
    async with aiofiles.open(file_name, "wb") as single_file:
        for id in ids:
            file_path = os.path.join(temp_dir, f"{file_name}.part{id}")
            async with aiofiles.open(file_path, "rb") as file:
                while True:
                    chunk = await file.read(10 * 1024 * 1024)
                    if not chunk:
                        break
                    await single_file.write(chunk)
            await delete_file(file_name, temp_dir, id)
    return True


async def delete_file(file_name: str, temp_dir: str, id: int) -> None:
    """
    Delete a file asynchronously.
    """
    file_path = os.path.join(temp_dir, f"{file_name}.part{id}")
    if os.path.exists(file_path):
        await async_remove(file_path)
