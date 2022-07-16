#!/usr/bin/env python3

"""
Create labwc theme based on the current Gtk theme

SPDX-License-Identifier: GPL-2.0-only

Copyright (C) @Misko_2083 2019
Copyright (C) Johan Malm 2019-2022
"""

import os
import errno
import argparse
from tokenize import tokenize, NUMBER, NAME, OP
from io import BytesIO
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

def parse(tokens):
    """
    Parse css color expression token list and return red/green/blue values
    Valid name-tokens include 'rgb' and 'rgba', whereas 'alpha', 'shade' and
    'mix' are ignored. @other-color references are still to be implemented.
    """
    nr_colors_to_parse = 0
    in_label = False
    color = []
    for toknum, tokval, _, _, _ in tokens:
        if '@' in tokval:
            in_label = True
            continue
        if toknum == NAME and in_label:
            color.clear()
            color.append(f"@{tokval}")
            return color
        if nr_colors_to_parse > 0:
            if toknum == OP and tokval in ')':
                print("warn: still parsing numbers; did not expect ')'")
            if toknum == NUMBER:
                color.append(tokval)
                nr_colors_to_parse -= 1
            continue
        if toknum == NAME and tokval in 'rgb':
            nr_colors_to_parse = 3
        elif toknum == NAME and tokval in 'rgba':
            nr_colors_to_parse = 4
    return color

def color_hex(color):
    """ return rrggbb color hex from list [r, g, b,...] """
    if not color:
        return "None"
    elif len(color) < 3:
        return f"{color[0]}"
    return '{:02x}{:02x}{:02x}'.format(*(int(x) for x in color[:3]))

def hex_from_expr(line):
    """ parse color expression to return hex style rrggbb """
    tokens = tokenize(BytesIO(line.encode('utf-8')).readline)
    color = parse(tokens)
    return color_hex(color)

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def add(file, key, color):
    if color is None:
        print(f"warn: no color for {key}")
        return
    file.write(f"{key}: #{color}\n")

def parse_section(lines, name):
    theme = {}
    inside = False
    for line in lines:
        if f"{name} {{" in line:
            inside = True
            continue
        if inside:
            if "}" in line or "{" in line:
                inside = False
                continue
            if 'color' not in line:
                continue
            key, value = line.strip().split(":", maxsplit=1)
            theme[f'{name}.{key.replace(" ", "")}'] = hex_from_expr(value)
    return theme

def resolve_labels(theme):
    for key, label in theme.items():
        if '@' in label:
            for tmp, value in theme.items():
                if tmp == label[1:]:
                    theme[key] = value
                    return resolve_labels(theme)
    return theme

def main():
    """ main """
    parser = argparse.ArgumentParser(prog="labwc-gtktheme")
    parser.add_argument("--css", help="dump css and exit", action='store_true')
    parser.add_argument("--colors", help="dump colors and exit", action='store_true')
    args = parser.parse_args()

    gset = Gtk.Settings.get_default()
    themename = gset.get_property("gtk-theme-name")
    css = Gtk.CssProvider.get_named(themename).to_string()

    if args.css:
        print(css)
        return

    lines = css.split("\n")
    theme = {}

    # Parse @define-color lines using syntax "@define-color <key> <value>"
    for line in lines:
        if "@define-color" not in line:
            continue
        x = line.split(" ", maxsplit=2)
        theme[x[1]] = hex_from_expr(x[2])

    # Add the color definitions in the headerbar{} and menu{} sections
    theme |= parse_section(lines, "headerbar")
    theme |= parse_section(lines, "menu")

    theme = resolve_labels(theme)

    # Set fallbacks
    # Most themes contain headerbar.border-top-color, but Materia does not
    if not 'headerbar.border-top-color' in theme.keys():
        theme[f'headerbar.border-top-color'] = theme["theme_bg_color"]

    if args.colors:
        for key, value in theme.items():
            print(f"{key}: {value}")
        return

    themename = 'GTK'
    themedir = os.getenv("HOME") + "/.local/share/themes/" + themename + "/openbox-3"
    mkdir_p(themedir)
    themefile = themedir + "/themerc"
    print(f"Create theme {themename} at {themedir}")

    with open(themefile, "w") as f:
        add(f, "window.active.title.bg.color", theme["theme_bg_color"])
        add(f, "window.inactive.title.bg.color", theme["theme_bg_color"])

        add(f, "window.active.label.text.color", theme["theme_text_color"])
        add(f, "window.inactive.label.text.color", theme["theme_text_color"])

        add(f, "window.active.border.color", theme["headerbar.border-top-color"])
        add(f, "window.inactive.border.color", theme["borders"])

        add(f, "window.active.button.unpressed.image.color", theme["theme_fg_color"])
        add(f, "window.inactive.button.unpressed.image.color", theme["theme_fg_color"])

        add(f, "menu.items.bg.color", theme["menu.background-color"])
        add(f, "menu.items.text.color", theme["theme_fg_color"])

        add(f, "menu.items.active.bg.color", theme["theme_fg_color"])
        add(f, "menu.items.active.text.color", theme["theme_bg_color"])

        add(f, "osd.bg.color", theme["theme_bg_color"])
        add(f, "osd.border.color", theme["theme_fg_color"])
        add(f, "osd.label.text.color", theme["theme_fg_color"])

    # TODO:
    # border.width: 1
    # padding.height: 3
    # menu.overlap.x: 0
    # menu.overlap.y: 0
    # window.label.text.justify: center
    # osd.border.width: 1

if __name__ == '__main__':
    main()
