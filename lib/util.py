def find_argument_in_line(line:str):
    which_param = 0
    mode = "firstparen"   # firstparen, argument, nesting, nestingignorenext
    nesting = []
    nest_chars = {"[":"]", "(":")", '"': '"', "'": "'"}
    tillnow = ""
    for c in line:
        tillnow += c
        if mode == "firstparen" and c == "(":
            mode = "argument"
        elif mode=="nesting":  # nesting will have at least the first nested character
            if c == nest_chars[nesting[-1]]:
                del nesting[-1]
            elif c == "\\" and ("'" in nesting or '"' in nesting):
                mode = "nestingignorenext"
            elif c in nest_chars.keys():
                nesting.append(c)
            if not nesting:
                mode = "argument"
        elif mode == "nestingignorenext":
            mode = "nesting"
        elif mode == "argument":
            if c in nest_chars.keys():
                nesting.append(c)
                mode = "nesting"
            elif c == ",":
                which_param += 1
    return which_param
assert find_argument_in_line('''card.draw_text(300''')==0
assert find_argument_in_line('''card.draw_text(300,''')==1
assert find_argument_in_line('''card.draw_text(300, 1''')==1
assert find_argument_in_line('''card.draw_text(300, 15''')==1
assert find_argument_in_line('''card.draw_text(300, 15, str(row.get("Power",''')==2
assert find_argument_in_line('''card.draw_text(300, 15, str(row.get("Power", "5"))+"/"+row.get("HP", "5")''')==2
assert find_argument_in_line('''card.draw_text(300, 15, str(row.get("Power", "5"))+"/"+row.get("HP", "5"), 75''')==3