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
    def gen_content(self, player):
        return "".join([f"""
            <rect id="{card.card_id}" x="{card.x}" y="{card.y}" width="{card.w}" height="{card.h}" fill="{"red" if card.owner == player else "green"}" stroke="red" pointer-events="all" cursor="pointer" />
            """ for card in self.cards])
    # This is a ui that is generated independant for each player
    @ui.refreshable
    def build(self, view):
        print("building the interactive mode", view)
        player = view.player
        view.content = self.gen_content(player)
        with ui.card() as card:
            view.interactive = ui.interactive_image('https://picsum.photos/640/360',
                content=view.content
            ).on('svg:pointerdown', lambda e: self.click_component(player, e))
            card.on('mouseup', lambda e: self.click_component_up(player))
            card.on('mousemove', lambda e: self.move_component(view, e))
        # TODO - clickdown should set ownership of object to current user
        # TODO clickup should undo ownership
        # TODO mouse drag
    def click_component(self, player, e):
        card_id = e.args['element_id']
        for card in self.cards:
            if card_id == card.card_id and card.owner == player:
                player.dragging = card
                player.dragging_point = e.args['image_x'], e.args['image_y']
                return
    def click_component_up(self, player):
        player.dragging = None
    def move_component(self, view, e):
        player = view.player
        if not player.dragging:
            return
        #point = e.args['image_x'], e.args['image_y']
        #amt = point[0]-player.dragging_point[0], point[1]-player.dragging_point[1]
        amt = e.args['movementX'], e.args['movementY']
        player.dragging.x += amt[0]
        player.dragging.y += amt[1]
        #player.dragging_point = point
        view.content = self.gen_content(player)
        view.interactive.content = view.content
        view.interactive.update()
        #self.build.refresh()
    async def set_view(self, table_view):
        if table_view.player not in self.players:
            self.join(table_view.player)
        table_view.player.current_virtual_table = self
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
    async def new_table(self, table_view):
        # Make table
        t = VirtualTable()
        self.tables[t.table_id] = t
        # Join table
        await t.set_view(table_view)
        # TODO this only refreshes the view for one player
        # If someone else is joined already they wont see the list update
        table_view.build.refresh()

tables = Tables()

# Model - each player has a separate one
# Doesn't hold any game specfic information, really a user
class Player:
    def __init__(self):
        self.player_id = str(uuid.uuid4())
        self.current_virtual_table = None
        self.table_view = None
        self.dragging = None
        self.dragging_point = None

# View - show all running tables with option to join one
# Once joined, show the table
# 1:1 with Player
class TableView:
    def __init__(self):
        self.player = Player()
        self.player.table_view = self
        self.content = ""
        self.interactive_content = None

    def rerender_view(self):
        self.content = self.player.current_virtual_table.gen_content(self.player)
        self.interactive.content = self.content
        self.interactive.update()

    @ui.refreshable
    async def build(self):
        print("building a table view")
        if self.player.current_virtual_table:
            self.player.current_virtual_table.build(self)
            ui.timer(0.02, lambda:self.rerender_view())
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

if __name__ == "__main__":
    @ui.page('/')
    async def main():
        view = TableView()
        with ui.card():
            await view.build()
    app.on_startup(main)
    ui.run(reload=platform.system() != 'Windows', native=False, title="Virtual Tabletop")