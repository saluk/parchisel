import platformdirs
import json
import os

appname = 'parchisel'
configfile = 'global_config.json'

class Profile:
    default_profile = {
        'last_project': None
    }
    def __init__(self):
        self.profile = self.default_profile.copy()
        self._profile_dir = platformdirs.user_config_dir(appname, False)+os.path.sep
        self.profile_path = self._profile_dir+configfile
        self.read()
    def read(self):
        print("reading profile", self.profile_path)
        data = {}

        if os.path.exists(self.profile_path):
            with open(self.profile_path) as f:
                data = json.loads(f.read())
        
        for k in self.profile:
            if k in data and type(data[k]) == type(self.profile[k]) or self.profile[k] == None or data[k] == None:
                self.profile[k] = data[k]
    def write(self):
        print("writing profile", self.profile_path)
        if not os.path.exists(self._profile_dir):
            os.mkdir(self._profile_dir)
        with open(self.profile_path, "w") as f:
            f.write(json.dumps(self.profile))

global_profile = Profile()