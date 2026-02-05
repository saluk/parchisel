# About

Parchisel is currently in very early development. It is
meant to be a set of tools which are useful when creating
board game prototypes.

Not everything in this readme is implemented - this
is very early on.

## Parchisel Component Creator

The component creator allows you to combine different
types of data with templates to quickly prepare graphics
files for use in board game prototypes (either digital
or physical). It's aim is to be as flexible and powerful
as possible, while making iteration quick.

The main concept is you define three types of information,
and the pipeline is saved for future iteration. The
three elements are: data sources, templates, and outputs

### Data Sources

A data source is a csv file, excel file, a link to 
an accessible google sheet, or even a python script
to generate data algorithmically. The data will be information
about each card or component in a game.

### Templates

Templates are python scripts which are run for each row in
the data files to generate the graphical elements.
Some drawing commands are included to make it pretty easy
to create templates; but since these are python scripts
almost anything is possible.

### Outputs

Define each type of output that is required. Most virtual
tabletops will want, for instance, a grid of card backs as
one image file, and a grid of card fronts as another image
file, for one set of cards. So you would define one output
for the front, and one output for the back - choosing the
appropriate data sources and templates for each.

In this way you can define multiple types of output for
the same set of cards, for instance to generate print and
play files alongside virtual tabletop images.

## Other tools

Here are some other tools I'm thinking about building:

- A simulation runner to allow easy creation of a game model
    which can then be tested, generating statistics about
    what is likely to happen in the game
- A digital playtesting board, similar to TTS or screentop.gg
    the main feature would be quick and repeatable generation
    of the files to be placed on the playtesting board,
    with a pretty stripped down set of controls and functions.

# Installation

- Install python
- pip install nicegui
- pip install pywebview
- pip install pillow

# Licenses + Acknowledgements

This tool was built on top of some great technology:
- NiceGUI - create web interfaces in python fast
- Pillow - image manipulation in python
- Python3 - and of course, python!

Includes fonts from Google Font:
https://openfontlicense.org/open-font-license-official-text/

# GameStateGraph thing
TODO - move keyboard from SingleStateUI to be a member of GameStateGraphUI so that it works for all components
TODO - hold ctrl for "select" to equal "tick". otherwise, "select" unticks and ticks single

# nearterm projects

ongoing - when loading a project, validate outputs have correct data and template values
ongoing - ensure project data is saved when necessary

TODO - python editor for data files
TODO - bug: if you change data so there are less cards than an output has configured, it gives an index error rather than fixing itself
TODO - component workflow: build components, auto configure outputs for digital/pnp
TODO - command pattern for undo/redo
TODO - edit output rows/cols
TODO - refresh python data sources ('refresh all' button is a workaround)
TODO - data source shortname configurable
TODO - edit .py data files
TODO - better filters for output preview: show output related to editor template, show outputs for a specified component, show outputs for a specified data source
TODO - render images to disk cache and load those for faster project load
TODO - this breaks the server: card.draw_text(25, 225, "<center>something</center", 320, 800, font_size=40)
TODO - templates are saved in project json with absolute file path
TODO - cleanup svg rendering cache
TODO - add svg string replacement
TODO - excel support
TODO - for online spreadsheets or .xsl/.odt files we'll need to select the 'sheet' for a data source
TODO - data view: show images in fields if it is an image
TODO - "<" character in draw text strings
TODO - output indexing should start at 1 for users
TODO - when creating a new csv, need to edit the headers
TODO - what is the template api?
TODO - more consideration on dirty the data
TODO - make output, and template paths relative to project
TODO - auto split output images if cards exceed max height (output could have sub images)
TODO - refactor with more nicegui native bindings
TODO - more ui.notify for CRUD (maybe put into Project)
TODO - widgets to edit current line of template
TODO - rich text: html/bbcode or markdown support in text
TODO - screentop export: don't tie spans to data source, just give them an offset 
TODO - screentop export: (allow single back image somehow)
TODO - screentop export: (ensure output images are suitable for rows and columns)
TODO - tests
TODO - notion integration

# Drawing revamp

- TODO recreate ancient artifacts
    - layers
    - use percentages as coordinates
    - relative coordinates inside a region
    - shape primitives
        - rect
        - polygon
        - curved corners
        - line (just a border)
    - fills
        - image background: image.makeShader
        - fill border too
        - fill origin (to have a pattern that spreads across the card in different shapes)
    - text
        - rotated
        - get size -> inject size elsewhere
        - rich text: change font on new line of text
        - icons: display a little bigger than the font text, maybe configure the font size for the icons
    - shaders
        - tinting
            - icons and fills

# Longterm Ideas
- Database backed project data for web hosted version
- SVG templates, svgeditor to edit them