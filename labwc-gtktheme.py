#!/usr/bin/env python3

# SPDX-License-Identifier: GPL-2.0-only

# Copyright (C) @Misko_2083 2019
# Copyright (C) Johan Malm 2019-2022

""" Create labwc theme to approximate current Gtk theme """

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
import os
import sys
import errno

def rgb2hex(line):
    """ find rgb() value and convert it to a 6-digit hex string """
    # TODO: improve parsing to cope with alpha(rgb(x,y,z), a);
    if "alpha" in line:
        return
    s = line.split("rgb(")
    rgb = s[-1].replace(");", "").split(",")
    r = hex(int(rgb[0]))[2:]
    g = hex(int(rgb[1]))[2:]
    b = hex(int(rgb[2]))[2:]
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
    gset = Gtk.Settings.get_default()
    themename = gset.get_property("gtk-theme-name")
    css = Gtk.CssProvider.get_named(themename).to_string()
#    print(css)
#    exit(1)
    lines = css.split("\n")

    theme = {}

    # parse @define-color lines using syntax "@define-color <key> <value>"
    for line in lines:
        if "@define-color" not in line:
            continue
        x = line.split(" ")
        theme['{}'.format(x[1])] = rgb2hex(line)

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
            line.strip()
            x = line.split(":")
            theme['csd.headerbar.{}'.format(x[0].replace(" ", ""))] = rgb2hex(line)

#    print_theme(theme)

    themename = 'GTK'
    themedir = os.getenv("HOME") + "/.local/share/themes/" + themename + "/openbox-3"
    mkdir_p(themedir)
    themefile = themedir + "/themerc"
    print("Create theme {} at {}".format(themename, themedir))

    f = open(themefile, "w")

    f.write("window.active.title.bg.color: #{}\n".format(theme["theme_bg_color"]))
    f.write("window.inactive.title.bg.color: #{}\n".format(theme["theme_bg_color"]))

    f.write("window.active.label.text.color: #{}\n".format(theme["theme_fg_color"]))
    f.write("window.inactive.label.text.color: #{}\n".format(theme["theme_fg_color"]))

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

    f.close()

if __name__ == '__main__':
    main()
