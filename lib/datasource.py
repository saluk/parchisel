import csv

class DataSource:
    def __init__(self, source):
        self.source = source
        self.cards = []
        self.fieldnames = []
    def load(self):
        pass
    def save(self):
        pass
class CSVData(DataSource):
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
    def load(self):
        g = {}
        with open(self.source) as f:
            exec(f.read(), g)
        self.cards = [row for row in g["rows"]()]
        for card in self.cards:
            for field in card:
                if field not in self.fieldnames:
                    self.fieldnames.append(field)