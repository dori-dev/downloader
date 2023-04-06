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
