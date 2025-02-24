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
        card_id = 0
        for card in self.cards:
            card["__id"] = card_id
            card_id += 1
        print(card)
    async def load_data(self):
        self.assign_ids()
    def save_data(self):
        pass
    def is_editable(self):
        return False

class CSVData(DataSource):
    type_label = "CSV File"
    async def load_data(self):
        self.cards = []
        reader = csv.DictReader((await self.read_file()).splitlines())
        for row in reader:
            self.cards.append(row)
        self.fieldnames = self.cards[0].keys()
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