import os
import datetime
import asyncio
import aiohttp
import aiofiles
from aiofiles.os import remove as os_remove

from functions import (
    get_headers,
    format_size,
    calc_file_chunks,
)


async def download_file(
        url: str,
        min_chunk_size: int = None,
        max_chunk_size: int = None,
        output: str = None
):
    try:
        headers = await get_headers(url)
    except KeyboardInterrupt:
        print('Downloading cancelled.')
    # content length
    content_length = headers.get('Content-Length', None)
    if content_length is None:
        raise Exception("Url file has no Content-Length header.")
    # file info
    file_name = os.path.basename(url)
    file_size = int(content_length)
    print(f"File size: {format_size(file_size)}")

    splitted_parts, chunk_size = calc_file_chunks(
        file_size,
        min_chunk_size,
        max_chunk_size,
    )
    file_total_parts = len(splitted_parts)
    print(
        f"File total parts: {file_total_parts} "
        f"(Each part is almost {format_size(chunk_size)}"
    )
    # downloading
    queue: asyncio.Queue[int] = asyncio.Queue(100)
