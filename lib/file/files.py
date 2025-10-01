# Load files from the filesystem or via url
# cache files accessed via url
# should we cache? probably during a given operation, 
# but each new operation might need to erase the cache
# to ensure information is fresh

import os
import aiohttp
import time
from hashlib import sha256

from lib import exceptions
from lib.file.online import ConvertOnlineLink

CACHE_TIME = 30     # After 30 seconds try to fetch again

def url_to_filename(url, char_limit=64):
    return sha256(url.encode()).hexdigest()[:char_limit]

class CacheEntry:
    def __init__(self, url, content):
        self.store_time = time.time()
        self.url = url
        self.content = content
class CacheMiss:
    pass
class Cache:
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        self.cache = {}
    def clear(self):
        self.cache.clear()
    def get(self, url, force_file=False):
        # See if it's in memory
        if url in self.cache and not force_file:
            entry = self.cache[url]
            if time.time() - entry.store_time < CACHE_TIME:
                return entry.content
            return CacheMiss
        if force_file:
            # See if its on the disc, load into memory
            file_path = f"{self.cache_dir}/{url_to_filename(url)}"
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    entry = self.cache[url] = CacheEntry(url, f.read())
                return entry.content
        return CacheMiss
    def set(self, url, content):
        self.cache[url] = CacheEntry(url, content)
        file_path = f"{self.cache_dir}/{url_to_filename(url)}"
        with open(file_path, "w") as f:
            f.write(content)

global_cache = Cache()

class File:
    TEXT="text"
    BYTES="bytes"
    def __init__(self, path, root_path = None):
        path = path.replace("\\", "/")
        self.path = path

        self.abs_path = None
        self.is_url = False
        self.is_api = False   # mark sources that are an api. source would be something like "google_api://{api_key}/{database_key}"
        self.edit_url = None
        self.link_data = None
        # If path is a url, save as url string
        
        if path.startswith("http://") or path.startswith("https://"):
            self.link_data = ConvertOnlineLink(path)
            self.abs_path = self.link_data.get_download_link()
            self.is_url = True
            self.is_api = self.link_data.is_api
            self.edit_url = self.link_data.get_edit_link()
        elif "://" in path:
            self.is_api = True
            self.abs_path = path
        elif self.path.startswith("/") or ":/" in self.path:
            self.abs_path = self.path.replace("\\","/")
        else:
            # Relative to given path
            if root_path!=None:
                self.abs_path = root_path + "/" + self.path.replace("\\", "/")
            # Relative to parchisel path
            else:
                self.abs_path = os.path.abspath(self.path).replace("\\", "/")

    def rel_path(self, root):
        if self.is_url or self.is_api:
            return self.abs_path
        path = self.abs_path
        print(root+"/", path)
        if root+"/" in path:
            return path.replace(root+"/", "")
        return path

    async def read(self, return_mode=None):
        if not return_mode:
            return_mode = File.TEXT
        if self.is_url:
            print("Read url ", self.abs_path)
            content = global_cache.get(self.abs_path)
            if content != CacheMiss:
                print(f"found {self.abs_path} in cache on first try")
                return content
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(self.abs_path) as response:
                        if response.status == 200:
                            if return_mode == File.TEXT:
                                content = await response.text()
                            elif return_mode == File.BYTES:
                                content = await response.read()
                            print(f"Accessed internet for {self.abs_path}")
                            global_cache.set(self.abs_path, content)
                except aiohttp.ClientConnectorError as e:
                    pass
            if content == CacheMiss:
                print(f"Checking file-backed cache for {self.abs_path}")
                content = global_cache.get(self.abs_path, force_file=True)
                if content == CacheMiss:
                    raise exceptions.NotifyException(f"Couldn't access url {self.abs_path} and not cached")
            return content
        with open(self.abs_path, "r") as f:
            return f.read()
        

    def write(self, text):
        if self.is_url:
            raise Exception("Cannot write to a url")
        with open(self.abs_path, "w") as f:
            f.write(text)