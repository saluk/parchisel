from nicegui import ui, app
import platform
import uuid

from lib.virtualtable.pixicanvas import PixiCanvas

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
    async def build(self, view):
        print("building the interactive mode", view)
        player = view.player
        with ui.card() as card:
            print("Make Pixi Canvas")
            view.canvas = PixiCanvas(400,400)
            def set_new_state(state):
                for scard in state:
                    for card in self.cards:
                        if scard['id'] == card.card_id:
                            card.x = scard['pos'][0]
                            card.y = scard['pos'][1]
            view.canvas.on('newstate', lambda e: set_new_state(e.args))
            ui.timer(0.1, lambda: view.canvas.run_method('setBunnyState', [
                {"vtid": c.card_id, "x": c.x, "y": c.y}
                for c in self.cards
            ]), immediate=False)
    async def set_view(self, table_view):
        if table_view.player not in self.players:
            self.join(table_view.player)
        table_view.player.current_virtual_table = self
        for player in self.players:
            player.table_view.build.refresh()
    def join(self, player):
        self.players.append(player)
        card = Card(0, 0, 50, 50, player)
        self.cards.append(card)
        print("Gave card to player")

# Model - Make one global instance
class Tables:
    def __init__(self):
        self.tables = {}
    def get_all(self):
        return [table for table in self.tables.values()]
    async def new_table(self, table_view):
        # Make table
        t = VirtualTable()
        self.tables[t.table_id] = t
        # Join table
        await t.set_view(table_view)
        # TODO this only refreshes the view for one player
        # If someone else is joined already they wont see the list update
        #for player in players:
        #    player.table_view.build.refresh()

tables = Tables()

players = []

# Model - each player has a separate one
# Doesn't hold any game specfic information, really a user
class Player:
    def __init__(self):
        self.player_id = str(uuid.uuid4())
        self.current_virtual_table = None
        self.table_view = None
        self.dragging = None
        self.dragging_point = None
        players.append(self)

# View - show all running tables with option to join one
# Once joined, show the table
# 1:1 with Player
class TableView:
    def __init__(self):
        self.player = Player()
        self.player.table_view = self
    @ui.refreshable
    async def build(self):
        ui.add_head_html('<script src="https://pixijs.download/release/pixi.js"></script>')
        print("building a table view")
        if self.player.current_virtual_table:
            await self.player.current_virtual_table.build(self)
            async def exit_game():
                self.player.current_virtual_table = None
                self.build.refresh()
            ui.button("Exit game").on_click(exit_game)
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

if __name__ in {"__main__", "__mp_main__"}:
    @ui.page('/')
    async def main():
        view = TableView()
        with ui.card():
            await view.build()
    app.on_startup(main)
    ui.run(reload=platform.system() != 'Windows', native=False, title="Virtual Tabletop", port=6812)
