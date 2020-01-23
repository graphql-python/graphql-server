import sys

if sys.version_info[:2] < (3, 4):
    collect_ignore_glob = ["*_asyncio.py"]
