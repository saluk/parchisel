import csv

class DataSource:
    type_label = "Unknown Data Source"
    def __init__(self, source):
        self.source = source
        self.cards = []
        self.fieldnames = []
    def load(self):
        pass
    def save(self):
        pass
class CSVData(DataSource):
    type_label = "CSV File"
    def load(self):
        self.cards = []
        with open(self.source) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.cards.append(row)
        self.fieldnames = self.cards[0].keys()
    def save(self):
        with open(self.source, "w") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writeheader()
            for card in self.cards:
                writer.writerow(card)
class PythonData(DataSource):
    type_label = "Python File (generator)"
    def load(self):
        g = {}
        with open(self.source) as f:
            exec(f.read(), g)
        self.cards = [row for row in g["rows"]()]
        for card in self.cards:
            for field in card:
                if field not in self.fieldnames:
                    self.fieldnames.append(field)

def get_class_for_source(source):
    if source.endswith(".csv"):
        return CSVData
    if source.endswith(".py"):
        return PythonData

def create_data_source(source):
    cls = get_class_for_source(source)
    return cls(source)