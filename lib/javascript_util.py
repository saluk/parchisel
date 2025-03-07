from nicegui import ui

async def element_run_javascript(element, code):
    return await ui.run_javascript(f"""
const element = getElement({element.id});
if (element === null || element === undefined) return null;
""" + code)