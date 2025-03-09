import os
import random
import json

import lib.datasource as datasource
from lib.template import Template
from lib.outputs import Output
from lib.files import File

class Project:
    def __init__(self):
        self.data_sources = []
        self.templates = {}
        self.outputs = {}
    async def load_data(self):
        [await d.load_data() for d in self.data_sources]
    def load_templates(self):
        raise NotImplemented
    async def dirty_outputs(self, for_templates=[], for_outputs=[]):
        any_dirty = False
        for output in self.outputs.values():
            if for_templates:
                all_used = set(await output.templates_used(self))
                all_templates = set(for_templates)
                print(all_used, all_templates)
                if not all_used.intersection(all_templates):
                    print("no intersection")
                    continue
            output.rendered_string = None
            # Dirty everything, but dont refresh view if we aren't watching this output
            print(f"output data name: {output.file_name}, outputs chosen:{for_outputs}")
            if not for_outputs or output.file_name in for_outputs:
                any_dirty = True
        print(f"was dirty: {any_dirty}")
        return any_dirty
    def render_outputs(self):
        for output in self.outputs.values():
            output.render(self)

    def get_data_source(self, fn):
        for ds in self.data_sources:
            if ds.source == fn:
                return ds
    async def remove_data_source(self, fn):
        ds = self.get_data_source(fn)
        if ds:
            self.data_sources.remove(ds)
            await self.dirty_outputs()
        self.save()
    async def rename_data_source(self, ds, source):
        i = self.data_sources.index(ds)
        new_ds = datasource.create_data_source(source, self)
        await new_ds.load_data()
        self.data_sources[i] = new_ds
        self.save()
    async def add_data_source(self, fn):
        fn = fn.strip()
        if self.get_data_source(fn):
            raise Exception("Datasource already linked")
        if not fn:
            raise Exception("No datasource entered")
        data_source = datasource.create_data_source(fn, self)
        try:
            await data_source.load_data()
        except Exception:
            raise
        self.data_sources.append(data_source)
        await self.dirty_outputs()
        self.save()
    async def create_data_source(self, fn):
        fn = fn.strip()
        if self.get_data_source(fn):
            raise Exception("Datasource already linked")
        if not fn:
            raise Exception("No datasource entered")
        f = File(fn, self.root_path)
        f.write("")
        return await self.add_data_source(fn)

    def add_template(self, template_name):
        t = Template(f"{self.get_template_path()}/{template_name}")
        t.save()
        self.templates[t.name] = t
        self.save()
        return t

    def add_output(self, output_name):
        new_out = Output("", output_name)
        # Choose a data source that isn't output yet, or pick at random
        used = set([out.data_source_name for out in self.outputs.values()])
        for s in self.data_sources:
            if s.source not in used:
                new_out.data_source_name = s.source
        if not new_out.data_source_name and used:
            new_out.data_source_name = random.choice(list(used))
        self.outputs[new_out.file_name] = new_out
        self.save()
        return new_out
    def remove_output(self, output):
        for key in self.outputs:
            if self.outputs[key] == output:
                del self.outputs[key]
                self.save()
                return
        raise Exception("Output not found")
    def rename_output(self, output, file_name):
        del self.outputs[output.file_name]
        output.file_name = file_name
        self.outputs[output.file_name] = output
        self.save()

    async def save_outputs(self):
        raise NotImplementedError()
    
    def save(self):
        """ Save project data """
        raise NotImplementedError()
    
    def load(self):
        """ Load project data """
        raise NotImplementedError()

class LocalProject(Project):
    def __init__(self, name, root_path):
        self.name = name
        self.root_path = root_path.replace("\\", "/")           # absolute path to project folder, no trailing slash
        self.output_path = "outputs"         # absolute or relative path to where to write outputs
        self.template_path = "templates"     # absolute or relative path to where to read/write templates
        self.data_path = "data"              # absolute or relative path for csv data
        self.image_path = "images"           # absolute or relative path for image files
        super().__init__()
    def create(self):
        """Call to actually create the files"""
        if os.path.exists(self.root_path):
            raise Exception(f"{self.root_path} already exists")
        os.mkdir(self.root_path)
        os.mkdir(self.rel_path(self.output_path))
        os.mkdir(self.rel_path(self.template_path))
        os.mkdir(self.rel_path(self.data_path))
        os.mkdir(self.rel_path(self.image_path))
        self.save()
    async def load(self):
        with open(f"{self.root_path}/prchsl_cc_proj.json") as f:
            d = json.loads(f.read())
        self.output_path = d["output_path"]
        self.template_path = d["template_path"]
        self.data_path = d["data_path"]
        self.image_path = d["image_path"]
        self.data_sources = []
        for source in d["data_sources"]:
            source = File(source, self.root_path).rel_path(self.root_path)
            print(source, self.root_path)
            self.data_sources.append(
                datasource.create_data_source(source, self)
            )
        for key in d["templates"]:
            self.templates[key] = Template(d["templates"][key])
        for key in d["outputs"]:
            self.outputs[key] = Output(**d["outputs"][key])
        await self.load_data()
    def save(self):
        d = {}
        d["output_path"] = self.output_path
        d["template_path"] = self.template_path
        d["data_path"] = self.data_path
        d["image_path"] = self.image_path
        d["data_sources"] = []
        for source in self.data_sources:
            d["data_sources"].append(File(source.source, self.root_path).rel_path(self.root_path))
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
                "template_field": o.template_field,
                "card_range": o.card_range,
                "component": o.component
            }
        txt = json.dumps(d)
        with open(f"{self.root_path}/prchsl_cc_proj.json", "w") as f:
            f.write(txt)
    def rel_path(self, path):
        if not path.startswith("/") and not ":" in path:
            return self.root_path + "/" + path
        return path
    def get_image_path(self):
        return self.rel_path(self.image_path)
    def get_template_path(self):
        return self.rel_path(self.template_path)
    def load_templates(self):
        tp = self.get_template_path()
        for template in os.listdir(tp):
            print(f"check template {template}")
            self.templates[template] = Template(f"{tp}/"+template)
    async def save_outputs(self):
        await self.load_data()
        await self.dirty_outputs()
        for output in self.outputs.values():
            print(f"Look at output {output}")
            if not output.rendered_string:
                print(f"render output {output}")
                await output.render(self)
            output.save(self.rel_path(self.output_path))