import csv

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

class CSVData(DataSource):
    type_label = "CSV File"
    async def load_data(self):
        self.cards = []
        reader = csv.DictReader((await self.read_file()).splitlines())
        for row in reader:
            self.cards.append(row)
        self.fieldnames = []
        if self.cards:
            self.field_names = self.cards[0].keys()
        await super().load_data()
    def save_data(self):
        file = File(self.source, self.project.root_path)
        with open(file.abs_path, "w") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writeheader()
            for card in self.cards:
                writer.writerow(card)
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
    source = File(source).abs_path
    print(source)
    if source.endswith(".csv") or source.endswith("format=csv"):
        return CSVData
    if source.endswith(".py"):
        return PythonData

def create_data_source(source, project):
    cls = get_class_for_source(source)
    return cls(source, project)