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
import re
import string
from tokenize import tokenize, NUMBER, STRING, NAME, OP
from io import BytesIO
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

def parse(tokens):
    """
      Parse css color expression token list and return red/green/blue values
       - [ ] @other-color
       - [x] rgb(r,g,b)
       - [ ] rgba(r,g,b,a)
       - [x] alpha(<color>,a)
       - [ ] shade(<color>,s)
       - [ ] mix(<color>,<color>,m)
    """

#    in_alpha = False
    nr_colors_to_parse = 0
    color = []

    for toknum, tokval, _, _, _ in tokens:
        if nr_colors_to_parse > 0:
            if toknum == OP and tokval in ')':
                print("warn: still parsing numbers; did not expect ')'")
            if toknum == NUMBER:
                color.append(tokval)
                nr_colors_to_parse -= 1
            continue
        if toknum == NAME and tokval in 'rgb':
            nr_colors_to_parse = 3
#        elif in_alpha and toknum == NUMBER and nr_colors_to_parse == 0:
#           # handle second argument of alpha()
#            color = [i * float(tokval) for i in color]
#            in_alpha = False
#        if toknum == NAME and tokval in 'alpha':
#            in_alpha = True
    return color

def rgba(color):
    if len(color) < 3:
        print("color is incomplete")
        return 0, 0, 0, 0
    if len(color) == 3:
        return color[0], color[1], color[2], 0
    if len(color) > 4:
        return color[0], color[1], color[2], color[3]

def hex_from_expr(line):
    """
      convert css color expression to 6-digit hex string, where an expression
      can be any of:
        - @other-color
        - rgb(r,g,b)
        - rgba(r,g,b,a)
        - alpha(<color>,a)
        - shade(<color>,s)
        - mix(<color>,<color>,m)
      and <color> is one of rgb(r,g,b), @other-color
    """

    # TODO: don't yet handle 'shade', 'mix', 'rgba' and '@other-color'
    if 'shade' in line or 'mix' in line or 'rgba' in line or '@' in line:
        return

    tokens = tokenize(BytesIO(line.encode('utf-8')).readline)
    color = parse(tokens)
    r, g, b, _ = rgba(color)
    r = hex(int(r))[2:]
    g = hex(int(g))[2:]
    b = hex(int(b))[2:]
    return "{}{}{}".format(r.zfill(2), g.zfill(2), b.zfill(2))

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def print_theme(theme):
    for key, value in theme.items():
        print("{}: {}".format(key, value))

def add(file, key, color):
    if color == None:
        print(f"warn: no color for {key}")
        return
    file.write(f"{key}: #{color}\n")

def main():
    """ main """
    parser = argparse.ArgumentParser(prog="labwc-gtktheme")
    parser.add_argument("--dump-css", help="dump css and exit", action='store_true')
    args = parser.parse_args()

    gset = Gtk.Settings.get_default()
    themename = gset.get_property("gtk-theme-name")
    css = Gtk.CssProvider.get_named(themename).to_string()

    if args.dump_css:
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

    # parse the .csd headerbar { } section
    inside = False
    for line in lines:
        if ".csd headerbar {" in line:
            inside = True
            continue
        if inside:
            if "}" in line or "{" in line:
                inside = False
                break
            line = line.strip()
            x = line.split(":", maxsplit=1)
            theme['csd.headerbar.{}'.format(x[0].replace(" ", ""))] = hex_from_expr(x[1])

#    print_theme(theme)

    themename = 'GTK'
    themedir = os.getenv("HOME") + "/.local/share/themes/" + themename + "/openbox-3"
    mkdir_p(themedir)
    themefile = themedir + "/themerc"
    print("Create theme {} at {}".format(themename, themedir))

    with open(themefile, "w") as f:
        add(f, "window.active.title.bg.color", theme["theme_bg_color"])
        add(f, "window.inactive.title.bg.color", theme["theme_bg_color"])

        add(f, "window.active.label.text.color", theme["theme_text_color"])
        add(f, "window.inactive.label.text.color", theme["theme_text_color"])

#        add(f, "window.active.border.color", theme["csd.headerbar.border-top-color"])
        add(f, "window.active.border.color", theme["borders"])
        add(f, "window.inactive.border.color", theme["borders"])

        add(f, "window.active.button.unpressed.image.color", theme["theme_fg_color"])
        add(f, "window.inactive.button.unpressed.image.color", theme["theme_fg_color"])

        add(f, "menu.items.bg.color", theme["theme_bg_color"])
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
