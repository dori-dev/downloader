import os
from functools import partial
import asyncio
import aiofiles

from functions import (
    get_headers,
    format_size,
    calc_file_chunks,
    download_part,
    delete_file,
    show_progress,
    merge_file_parts,
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
    total_parts = len(splitted_parts)
    print(
        f"File total parts: {total_parts} "
        f"(Each part is almost {format_size(chunk_size)}"
    )
    # downloading
    queue: asyncio.Queue[int] = asyncio.Queue(100)
    async with aiofiles.tempfile.TemporaryDirectory() as temp_dir:
        download = partial(download_part, url, temp_dir, file_name, queue)
        download_future: asyncio.Future = asyncio.gather(
            *[
                download(id + 1, from_, to)
                for id, (from_, to) in enumerate(splitted_parts)
            ],
            show_progress(queue, file_size, total_parts)
        )
        print("Download started...")
        downloaded = False
        saved = False
        try:
            await download_future
            downloaded = True
        except Exception:
            downloaded = False
        if downloaded:
            print("Merging parts...")
            saved = await merge_file_parts(file_name, temp_dir, total_parts)
        else:
            remove = partial(delete_file, file_name, temp_dir)
            print("Deleting the partial downloaded parts...")
            delete_file_future = asyncio.gather(
                *[
                    remove(id+1)
                    for id in range(total_parts)
                ]
            )
            await delete_file_future
    return saved
