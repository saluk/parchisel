# Virtual Table Notes

Object/Update diagram

-Table-
'A single game being played'
- fields
    - id
    - tableviews: all the tableviewers looking at us
    - max_players: after this, other players are spectators
    - players: all the players registered as in the game
        (may or may not be the same as the players attached to tableviews)
- methods
    - join_game(player): player attempts to join the game as a player
        if player already joined - pass
        if max_players - fail
    - exit_game(player): player quits game
    - add_tableview(tableview)
    - remove_tableview(tableview)
    - player_action: update the table somehow, update all of the tableviews with new state

-TableView-
'A players view of a Table'
- fields
    - id(accessor): identified by table.id, player.id
    - table: table we are viewing
    - player: the player who is looking
- views
    - canvas: create the canvas that will show the player's view of the table
    - update_canvas: update the existing canvas with the new table model

-TableList-
'A view of all accessible tables. Only one.'
- fields
    - players: the players looking at the list
    - tables: all of the current tables running
- methods
    - add_table: create a new Table, update players looking
    - delete_table: delete a table, update players looking
- views
    - Show list of joinable games, mark the ones player is already participating in
    - Show tableview canvas view

-Player-
'A player'
- fields
    - id
    - tables: tables we are participating in
    - tableview: tableview we are looking at
    - nicegui.client: which client is currently connected to this player
- methods:
    - create: created when nicegui.Client connects
    - connect_to_table(table):
        remove tableview if exists from player and table
        table.join_game(player)
        create tableview
        table.add_tableview(tableview)
    - disconnect: called when nicegui.Client disconnects
        if tableview:
            tableview.table.remove_tableview(tableview)