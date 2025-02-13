import os

import lib.datasource as datasource

class Template:
    def __init__(self, filename):
        self.filename = filename
        self._code = None
    @property
    def code(self):
        if not self._code:
            self.load()
        return self._code
    @code.setter
    def code(self, code):
        self._code = code
    @property
    def reload_code(self):
        self.load()
        return self._code
    def load(self):
        with open(self.filename,"r") as f:
            self._code = f.read()
    def save(self):
        with open(self.filename,"w") as f:
            f.write(self._code)

class Project:
    def __init__(self):
        self.data_sources = []
        self.templates = {}
        self.outputs = {}
    def load_data(self):
        [d.load() for d in self.data_sources]
    def load_templates(self):
        for template in os.listdir("data/templates"):
            self.templates[template] = Template("data/templates/"+template)
    def render_outputs(self):
        for output in self.outputs.values():
            output.render(self)

    def get_data_source(self, fn):
        for ds in self.data_sources:
            if ds.source == fn:
                return ds
    def remove_data_source(self, fn):
        ds = self.get_data_source(fn)
        if ds:
            self.data_sources.remove(ds)
    def add_data_source(self, fn):
        fn = fn.strip()
        if self.get_data_source(fn):
            raise Exception("Datasource already linked")
        if not fn:
            raise Exception("No datasource entered")
        # This could be a more elaborate google sheet implementation
        if fn.startswith("https://docs.google.com/"):
            raise Exception("google docs not yet supported")
        # These functions add files from a url that can be redownloaded
        elif fn.startswith("http"):
            raise Exception("url download not yet supported")
        # These functions add files from the local filesystem
        else:
            if not os.path.exists(fn):
                raise Exception("File not found")
            data_source = None
            if fn.endswith(".csv"):
                data_source = datasource.CSVData(fn)
            elif fn.endswith(".py"):
                data_source = datasource.PythonData(fn)
            if not data_source:
                raise Exception("Error creating data source")
            data_source.load()
            self.data_sources.append(data_source)
    def save_outputs(self):
        for output in self.outputs.values():
            output.save()