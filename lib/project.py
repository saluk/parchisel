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
    def dirty_outputs(self, for_templates=[], for_outputs=[]):
        any_dirty = False
        for output in self.outputs.values():
            if for_templates:
                all_used = set(["data/templates/"+used for used in output.templates_used(self)])
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
        for output in self.outputs.values():
            print(f"Look at output {output}")
            if not output.rendered_string:
                print(f"render output {output}")
                await output.render(self)
            output.save()