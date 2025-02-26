from nicegui import ui, app
import platform
import uuid

# Model
class Card:
    def __init__(self, x, y, w, h, owner = None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.card_id = str(uuid.uuid4())
        self.owner = owner

# Model - Make one for each game running
class VirtualTable:
    def __init__(self):
        self.table_id = str(uuid.uuid4())
        self.players = []
        self.cards = []
    # This is a ui that is generated independant for each player
    @ui.refreshable
    def build(self, player):
        self.interactive = ui.interactive_image('https://picsum.photos/640/360',
            content="".join([f"""
            <rect id="{card.card_id}" x="{card.x}" y="{card.y}" width="{card.w}" height="{card.h}" fill="{"red" if card.owner == player else "green"}" stroke="red" pointer-events="all" cursor="pointer" />
            """ for card in self.cards])
        ).on('svg:pointerdown', lambda e: self.click_component(player, e.args['element_id']))
        # TODO - clickdown should set ownership of object to current user
        # TODO clickup should undo ownership
        # TODO mouse drag
    def click_component(self, player, card_id):
        for card in self.cards:
            print(repr(card_id), repr(card.card_id))
            if card_id == card.card_id and card.owner == player:
                print("move")
                card.x += 10
        self.build.refresh()
    def set_view(self, table_view):
        if table_view.player not in self.players:
            self.join(table_view.player)
        table_view.player.current_virtual_table = self
        table_view.build.refresh()
    def join(self, player):
        self.players.append(player)
        card = Card(0, 0, 50, 50, player)
        self.cards.append(card)
        self.build.refresh()

# Model - Make one global instance
class Tables:
    def __init__(self):
        self.tables = {}
    def get_all(self):
        return [table for table in self.tables.values()]
    def new_table(self, table_view):
        # Make table
        t = VirtualTable()
        self.tables[t.table_id] = t
        # Join table
        t.set_view(table_view)
        table_view.build.refresh()

tables = Tables()

# Model - each player has a separate one
# Doesn't hold any game specfic information, really a user
class Player:
    def __init__(self):
        self.player_id = str(uuid.uuid4())
        self.current_virtual_table = None
        self.table_view = None

# View - show all running tables with option to join one
# Once joined, show the table
# 1:1 with Player
class TableView:
    def __init__(self):
        self.player = Player()
        self.player.table_view = self

    @ui.refreshable
    def build(self):
        print("building")
        if self.player.current_virtual_table:
            print("Current table")
            self.player.current_virtual_table.build(self.player)
        else:
            print("New table")
            self.build_list()

    def build_list(self):
        with ui.card():
            for table in tables.get_all():
                ui.button(f"Join {table.table_id}").on_click(lambda:table.set_view(self))
            print("Adding new table button")
            ui.label("BLAH")
            ui.button("New Table").on_click(lambda:tables.new_table(self))

@ui.page('/')
async def main():
    view = TableView()
    with ui.card():
        view.build()

if __name__ == "__main__":
    app.on_startup(main)
    ui.run(reload=platform.system() != 'Windows', native=False, title="Virtual Tabletop")