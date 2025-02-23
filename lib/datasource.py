import csv

from nicegui import ui

from lib.files import File

class DataSource:
    type_label = "Unknown Data Source"
    def __init__(self, source):
        self.source = source
        self.cards = []
        self.fieldnames = []
    async def read_file(self):
        file = File(self.source)
        n = None
        if file.is_url:
            n = ui.notification("Loading...", position="top-right", type="ongoing")
        content = await file.read()
        if n:
            n.dismiss()
        return content
    async def load_data(self):
        pass
    def save_data(self):
        pass
class CSVData(DataSource):
    type_label = "CSV File"
    async def load_data(self):
        self.cards = []
        reader = csv.DictReader((await self.read_file()).splitlines())
        for row in reader:
            self.cards.append(row)
        self.fieldnames = self.cards[0].keys()
    def save_data(self):
        with open(self.source, "w") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writeheader()
            for card in self.cards:
                writer.writerow(card)
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

def get_class_for_source(source):
    source = File(source).abs_path
    print(source)
    if source.endswith(".csv") or source.endswith("format=csv"):
        return CSVData
    if source.endswith(".py"):
        return PythonData

def create_data_source(source):
    cls = get_class_for_source(source)
    return cls(source)