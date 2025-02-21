import os
import json

import lib.datasource as datasource
from lib.template import Template
from lib.outputs import Output

# A project consists of:
#   A set of data sources (linked to local or remote files, or database links)
#   A set of templates (may be backed to local files, or a database)
#   A set of outputs (the filenames to generate, in local mode files 
#       are output to a local folder)
#   A set of image stores (local folder to search or a name linked to a image url)
#   location project data is stored (local json file, or database index in db mode)
#   local project only:
#       output folder
#       templates folder
#       default data source folder
#       default image folder

# To init a new LOCAL project
# - choose a root folder and a name for the project
# - create a project folder to hold data
# - create a subfolder for outputs, templates, sources, and images
# - create a json file for the project in that folder (prchsl_cc_proj.json)
#   save the local project data to the json

class Project:
    def __init__(self):
        self.data_sources = []
        self.templates = {}
        self.outputs = {}
    def load_data(self):
        [d.load() for d in self.data_sources]
    def load_templates(self):
        raise NotImplemented
    def dirty_outputs(self, for_templates=[], for_outputs=[]):
        any_dirty = False
        for output in self.outputs.values():
            if for_templates:
                all_used = set(output.templates_used(self))
                all_templates = set(for_templates)
                print(all_used, all_templates)
                if not all_used.intersection(all_templates):
                    continue
            output.rendered_string = None
            # Dirty everything, but dont refresh view if we aren't watching this output
            if not for_outputs or output.data_source_name in for_outputs:
                any_dirty = True
        return any_dirty
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
            self.dirty_outputs()
    def rename_data_source(self, ds, source):
        i = self.data_sources.index(ds)
        new_ds = datasource.create_data_source(source)
        new_ds.load()
        self.data_sources[i] = new_ds
    def add_data_source(self, fn):
        fn = fn.strip()
        if self.get_data_source(fn):
            raise Exception("Datasource already linked")
        if not fn:
            raise Exception("No datasource entered")
        data_source = datasource.create_data_source(fn)
        try:
            data_source.load()
        except Exception:
            raise
        self.data_sources.append(data_source)
        self.dirty_outputs()

    def remove_output(self, output):
        for key in self.outputs:
            if self.outputs[key] == output:
                del self.outputs[key]
                return
        raise Exception("Output not found")
    def rename_output(self, output, file_name):
        del self.outputs[output.data_source_name]
        output.file_name = file_name
        self.outputs[output.file_name] = output

    async def save_outputs(self):
        raise NotImplemented

class LocalProject(Project):
    def __init__(self, name, root_path):
        self.name = name
        self.root_path = root_path           # absolute path to project folder, no trailing slash
        self.output_path = "outputs"         # absolute or relative path to where to write outputs
        self.template_path = "templates"     # absolute or relative path to where to read/write templates
        self.data_path = "data"              # absolute or relative path for csv data
        self.image_path = "images"           # absolute or relative path for image files
        super().__init__()
    def create(self):
        """Call to actually create the files"""
    def load(self):
        with open(f"{self.root_path}/prchsl_cc_proj.json") as f:
            d = json.loads(f.read())
        self.output_path = d["output_path"]
        self.template_path = d["template_path"]
        self.data_path = d["data_path"]
        self.image_path = d["image_path"]
        self.data_sources = []
        for source in d["data_sources"]:
            self.data_sources.append(
                datasource.create_data_source(source)
            )
        for key in d["templates"]:
            self.templates[key] = Template(d["templates"][key])
        for key in d["outputs"]:
            self.outputs[key] = Output(**d["outputs"][key])
        self.load_data()
    def save(self):
        d = {}
        d["output_path"] = self.output_path
        d["template_path"] = self.template_path
        d["data_path"] = self.data_path
        d["image_path"] = self.image_path
        d["data_sources"] = []
        for source in self.data_sources:
            d["data_sources"].append(source.source)
        d["templates"] = {}
        for key in self.templates:
            d["templates"][key] = self.templates[key].filename
        d["outputs"] = {}
        for key in self.outputs:
            o = self.outputs[key]
            d["outputs"][key] = {
                "data_source_name": o.data_source_name,
                "file_name": o.file_name,
                "template_name": o.template_name,
                "template_field": o.template_field
            }
        with open(f"{self.root_path}/prchsl_cc_proj.json", "w") as f:
            f.write(json.dumps(d))
    def rel_path(self, path):
        if not path.startswith("/") and not ":" in path:
            return self.root_path + "/" + path
        return path
    def get_image_path(self):
        return self.rel_path(self.image_path)
    def load_templates(self):
        tp = self.rel_path(self.template_path)
        for template in os.listdir(tp):
            self.templates[template] = Template(f"{tp}/"+template)
    async def save_outputs(self):
        for output in self.outputs.values():
            print(f"Look at output {output}")
            if not output.rendered_string:
                print(f"render output {output}")
                await output.render(self)
            output.save(self.rel_path(self.output_path))