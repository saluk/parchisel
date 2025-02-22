# Load files from the filesystem or via url
# cache files accessed via url
# should we cache? probably during a given operation, 
# but each new operation might need to erase the cache
# to ensure information is fresh

import os
import aiohttp
from nicegui import ui

class Cache:
    def __init__(self):
        self.cache = {}

global_cache = Cache()

def url_to_filename(url):
    return url.replace("http://", "HTTP").repalce("https://","HTTPS").replace("/","_s_")

class File:
    TEXT="text"
    BYTES="bytes"
    def __init__(self, path, root_path = None):
        path = path.replace("\\", "/")
        self.path = path

        self.url_path = None
        self.abs_path = None
        # If path is a url, save as url string
        
        if path.startswith("http://") or path.startswith("https://"):
            self.url_path = path
        elif self.path.startswith("/") or ":/" in self.path:
            self.abs_path = self.path
        else:
            # Relative to given path
            if root_path:
                self.abs_path = self.root_path + "/" + self.path
            # Relative to parchisel path
            else:
                self.abs_path = os.path.abspath(self.path)

    async def read(self, return_mode=None):
        if not return_mode:
            return_mode = File.TEXT
        if self.url_path:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url_path) as response:
                    if return_mode == File.TEXT:
                        return await response.text()
                    elif return_mode == File.BYTES:
                        return await response.read()
        with open(self.abs_path, "r") as f:
            return f.read()
        

    def write(self, text):
        if self.url_path:
            raise Exception("Cannot write to a url")
        with open(self.abs_path, "w") as f:
            f.write(text) 