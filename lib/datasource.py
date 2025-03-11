import csv
import shutil

from nicegui import ui

from lib.files import File

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
    def change_headers(self, newheaders):
        field_names = [x.strip() for x in newheaders.split(",")]
        assert len(field_names) == len(self.fieldnames)
        for c in self.cards:
            for i in range(len(self.fieldnames)):
                old = self.fieldnames[i]
                new = field_names[i]
                v = c[old]
                del c[old]
                c[new] = v
        self.fieldnames = field_names
    def change_header(self, old_name, new_name):
        assert(old_name in self.fieldnames)
        i = self.fieldnames.index(old_name.strip())
        self.fieldnames[i] = new_name.strip()
        for c in self.cards:
            v = c[old_name]
            del c[old_name]
            c[new_name] = v

class CSVData(DataSource):
    type_label = "CSV File"
    async def load_data(self):
        print("loading csv data")
        self.cards = []
        reader = csv.DictReader((await self.read_file()).splitlines())
        for row in reader:
            self.cards.append(row)
        self.fieldnames = reader.fieldnames
        await super().load_data()
    def save_data(self):
        file = File(self.source, self.project.root_path)
        # Don't corrupt file if there is an error
        try:
            with open(file.abs_path+".temp", "w", newline="") as csvfile:
                print("writing csv:", id(self), self.fieldnames)
                writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
                writer.writeheader()
                for card in self.cards:
                    writer.writerow(card)
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

def get_class_for_source(source):
    file = File(source)
    print(source)
    # Currontly only supporting online files that convert to csv
    if source.endswith(".csv") or file.is_url:
        return CSVData
    if source.endswith(".py"):
        return PythonData

def create_data_source(source, project):
    cls = get_class_for_source(source)
    return cls(source, project)