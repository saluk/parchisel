# Load files from the filesystem or via url
# cache files accessed via url
# should we cache? probably during a given operation, 
# but each new operation might need to erase the cache
# to ensure information is fresh

import os
import aiohttp
import re

class Cache:
    def __init__(self):
        self.cache = {}

global_cache = Cache()

def url_to_filename(url):
    return url.replace("http://", "HTTP").repalce("https://","HTTPS").replace("/","_s_")

def convert_google_sheet(url):
    print("convert", url)
    if "docs.google.com/spreadsheets/" in url:
        spreadsheet_ids = re.findall("docs\.google.com\/spreadsheets\/d\/(.*?)\/", url)
        if not spreadsheet_ids:
            # Well, we tried
            return url
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_ids[0]}/export?format=csv"
    return url

class File:
    TEXT="text"
    BYTES="bytes"
    def __init__(self, path, root_path = None):
        path = path.replace("\\", "/")
        self.path = path

        self.abs_path = None
        self.is_url = False
        # If path is a url, save as url string
        
        if path.startswith("http://") or path.startswith("https://"):
            self.abs_path = convert_google_sheet(path)
            self.is_url = True
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
        if self.is_url:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.abs_path) as response:
                    if return_mode == File.TEXT:
                        return await response.text()
                    elif return_mode == File.BYTES:
                        return await response.read()
        with open(self.abs_path, "r") as f:
            return f.read()
        

    def write(self, text):
        if self.is_url:
            raise Exception("Cannot write to a url")
        with open(self.abs_path, "w") as f:
            f.write(text) 