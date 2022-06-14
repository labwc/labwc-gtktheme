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
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

def tokenize(buf):
    """
      Tokenize nested color definitions such as alpha(rgb(r,g,b),a)
      to ['alpha','rgb','r','g','b','a'], ignoring commas and parenthesis,
      and return the list of tokens
    """
    pos = 0
    length = len(buf)
    tokens = []
    while pos < length:
        char = buf[pos]
        if char in '(),':
            # special characters
            pass
        elif char in string.digits + '.':
            # numbers
            regex = re.compile(r'\d*[.]?\d*')
            match = regex.search(buf, pos)
            if match:
                value = match.group()
                tokens.append(value)
                pos += len(value)
                continue
        elif char in string.ascii_letters:
            # idents
            regex = re.compile(r'rgb|rgba|alpha|shade|mix')
            match = regex.search(buf, pos)
            if match:
                value = match.group()
                pos += len(value)
                tokens.append(value)
                continue
        pos += 1
    return tokens

def rgb(tokens):
    # TODO: check that there are enough elements in list
    return int(tokens[0]), int(tokens[1]), int(tokens[2])

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
    r = 0; g = 0; b = 0
    in_alpha = False
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in 'rgb':
            r, g, b = rgb(tokens[i+1:])
            i += 3
        elif in_alpha:
            # handle 2nd argument of alpha(X, Y)
            r *= float(t); g *= float(t); b *= float(t)
            in_alpha = False
        elif t in 'alpha':
            in_alpha = True
        i += 1
    return r, g, b

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

    tokens = tokenize(line)
    r, g, b = parse(tokens)
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
        #add(f, "window.active.title.bg.color", theme["theme_bg_color"])
        f.write("window.active.title.bg.color: #{}\n".format(theme["theme_bg_color"]))
        f.write("window.inactive.title.bg.color: #{}\n".format(theme["theme_bg_color"]))

        f.write("window.active.label.text.color: #{}\n".format(theme["theme_text_color"]))
        f.write("window.inactive.label.text.color: #{}\n".format(theme["theme_text_color"]))

        try:
            f.write("window.active.border.color: #{}\n".format(theme["csd.headerbar.border-top-color"]))
        except:
            f.write("window.active.border.color: #{}\n".format(theme["borders"]))
        f.write("window.inactive.border.color: #{}\n".format(theme["borders"]))

        f.write("window.active.button.unpressed.image.color: #{}\n".format(theme["theme_fg_color"]))
        f.write("window.inactive.button.unpressed.image.color: #{}\n".format(theme["theme_fg_color"]))

        f.write("menu.items.bg.color: #{}\n".format(theme["theme_bg_color"]))
        f.write("menu.items.text.color: #{}\n".format(theme["theme_fg_color"]))

        f.write("menu.items.active.bg.color: #{}\n".format(theme["theme_fg_color"]))
        f.write("menu.items.active.text.color: #{}\n".format(theme["theme_bg_color"]))

        f.write("osd.bg.color: #{}\n".format(theme["theme_bg_color"]))
        f.write("osd.border.color: #{}\n".format(theme["theme_fg_color"]))
        f.write("osd.label.text.color: #{}\n".format(theme["theme_fg_color"]))

    # TODO:
    # border.width: 1
    # padding.height: 3
    # menu.overlap.x: 0
    # menu.overlap.y: 0
    # window.label.text.justify: center
    # osd.border.width: 1

if __name__ == '__main__':
    main()
