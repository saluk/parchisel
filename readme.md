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



# TODO 
- ensure project data is saved when necessary
- edit output rows/cols/width/height
- refactor with more nicegui native bindings
- more ui.notify for CRUD (maybe put into Project)
- edit csv files
- widgets to edit current line of template
- icons in draw_text positioned correctly

# Longterm Ideas
- Database backed project data for web hosted version
- SVG templates, svgeditor to edit them