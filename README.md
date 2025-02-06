# Introduction

`labwc-gtktheme.py` - A tool to parse the current [GTK theme], particularly
[colors] and produce an [openbox]/[labwc] theme.

Set the theme to `GTK` in your `~/.config/labwc/rc.xml` to use it.

```
<theme>
  <name>GTK</name>
</theme>
```

## TODO

- [ ] Resolve @labels in @define-color prior to parsing in order to support shade()
- [ ] Support shade() - not that it makes a difference to most themes, but there
      are some that look better if we parse it

[GTK theme]: https://docs.gtk.org/gtk3/css-overview.html
[colors]: https://docs.gtk.org/gtk3/css-overview.html#colors
[openbox]: http://openbox.org/
[labwc]: https://github.com/labwc/labwc
