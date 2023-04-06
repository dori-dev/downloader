import argparse
import asyncio
from download import download_file


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='File Downloader.',
    )
    parser.add_argument(
        "url",
        metavar="URL",
        type=str,
        help='URL to download',
    )
    parser.add_argument(
        '-min',
        '--min-chunk-size',
        type=int,
        help='Minimum file chunk size(default: 10MB)',
    )
    parser.add_argument(
        '-max',
        '--max-chunk-size',
        type=int,
        help='Maximum file chunk size(default: 100MB)',
    )
    parser.add_argument(
        '-o',
        '--output',
        type=str,
        help="Output file path (default: current working directory)",
    )
    args = parser.parse_args()
    if args.url:
        saved = asyncio.run(
            download_file(
                url=args.url,
                min_chunk_size=args.min_chunk_size,
                max_chunk_size=args.max_chunk_size,
                output=args.output,
            )
        )
        if saved:
            print('File download completed.')
        else:
            print('File download failed!')
