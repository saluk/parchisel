import csv
import shutil
from collections import defaultdict

from nicegui import ui

from lib.file import File

class DataSource:
    type_label = "Unknown Data Source"
    def __init__(self, source, project):
        self.source = source
        self.cards = []   # Simple dictionaries
        self.fieldnames = []
        self.project = project
    async def read_file(self):
        file = File(self.source, self.project.root_path)
        n = None
        if file.is_url:
            n = ui.notification("Loading...", position="top-right", type="ongoing")
        content = await file.read()
        if n:
            n.dismiss()
        return content
    def assign_ids(self):
        if "__id" not in self.fieldnames:
            self.fieldnames.append("__id")
        card_id = 0
        for card in self.cards:
            card["__id"] = card_id
            card_id += 1
    async def load_data(self):
        self.assign_ids()
    def save_data(self):
        pass
    def is_editable(self):
        return False
    def create_blank_field(self):
        fieldname = "blank_"+str(len(self.fieldnames))
        self.fieldnames.append(fieldname)
        for c in self.cards:
            c[fieldname] = ""
        self.assign_ids()
        print("created new field", self.fieldnames, id(self))
    def create_blank_card(self):
        d = {}
        for fieldname in self.fieldnames:
            d[fieldname] = ""
        self.cards.append(d)
        self.assign_ids()
    def rename_column(self, old_name, new_name):
        assert(old_name in self.fieldnames)
        i = self.fieldnames.index(old_name.strip())
        self.fieldnames[i] = new_name.strip()
        for c in self.cards:
            v = c[old_name]
            del c[old_name]
            c[new_name] = v
    def delete_column(self, old_name):
        assert(old_name in self.fieldnames)
        i = self.fieldnames.index(old_name.strip())
        del self.fieldnames[i]
        for c in self.cards:
            del c[old_name]
    def delete_card_matching(self, dict):
        for c in self.cards:
            if all([c[k]==dict[k] for k in dict]):
                self.cards.remove(c)
                return

# Used for in-place data
class TempDataSource(DataSource):
    def __init__(self):
        super().__init__("", None)
        self.fieldnames = []
        self.num_fields = 0
        def next():
            self.num_fields += 1
            return f"field_{self.num_fields}"
        self.cards = [defaultdict(next)]

    async def read_file(self):
        return ""

class CSVData(DataSource):
    type_label = "CSV File"
    async def load_data(self):
        print("loading csv data")
        self.cards = []
        reader = csv.DictReader((await self.read_file()).splitlines())
        for row in reader:
            if row:
                print(row)
                self.cards.append(row)
        self.fieldnames = reader.fieldnames or []
        await super().load_data()
    def save_data(self):
        file = File(self.source, self.project.root_path)
        # Don't corrupt file if there is an error
        try:
            with open(file.abs_path+".temp", "w", newline="") as csvfile:
                print("writing csv:", id(self), self.fieldnames)
                fieldnames = [n for n in self.fieldnames if not n.startswith("__")]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for card in self.cards:
                    writer.writerow({key:card[key] for key in card if not key.startswith("__")})
        except:
            raise
        shutil.move(file.abs_path+".temp", file.abs_path)
    def is_editable(self):
        if File(self.source).is_url:
            return False
        return True
    
class PythonData(DataSource):
    type_label = "Python File (generator)"
    async def load_data(self):
        g = {}
        exec(await self.read_file(), g)
        self.cards = [row for row in g["rows"]()]
        for card in self.cards:
            for field in card:
                if field not in self.fieldnames:
                    self.fieldnames.append(field)
        await super().load_data()

# TODO fill this out
class APIData(DataSource):
    type_label = "API Data Source"
    # probably need an api key or some other auth data
    # connect to api to read the rows into our object representation
    async def load_data(self):
        pass
    # TODO waaaay later, we can use iframe editors for most things. but we could make a unified interface
    # for services that have an api
    async def save_data(self):
        pass

def get_class_for_source(source):
    file = File(source)
    print(source)
    # Currontly only supporting online files that convert to csv
    if file.is_api:
        return APIData
    if source.endswith(".csv") or file.is_url:
        return CSVData
    if source.endswith(".py"):
        return PythonData

def create_data_source(source, project):
    cls = get_class_for_source(source)
    return cls(source, project)