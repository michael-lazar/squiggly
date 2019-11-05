"""
            How a Widget’s Size is Determined
|-------------|------------------------|------------------------|
| sizing mode |         width          |        height          |
|-------------|------------------------|------------------------|
| 'box'       | container decides      | container decides      |
| 'flow'      | container decides      | widget’s rows() method |
| 'fixed'     | widget’s pack() method | widget’s pack() method |
|-------------|------------------------|------------------------|
"""
import logging

import urwid

logger = logging.getLogger(__name__)


class EnhancedWidget(urwid.Widget):
    """
    Extend the urwid base Widget with some custom behavior.
    """

    attr_name = None
    focus_name = None

    def render(self, size, focus=False):
        """
        Apply the class attr_name and focus_name on top of the widget canvas.

        This is an alternative way of doing AttrMap(widget, ...) without
        needing to wrap every instance of the class with an AttrMap.
        """
        mode = ["FIXED", "FLOW", "BOX"][len(size)]
        logger.debug(f"Rendering {self} as {mode} (focus={focus})")

        if focus and self.focus_name is not None:
            attr_map = {None: self.focus_name}
        elif self.attr_name:
            attr_map = {None: self.attr_name}
        else:
            attr_map = None

        canvas = super().render(size, focus=focus)
        if attr_map is not None:
            canvas = urwid.CompositeCanvas(canvas)
            canvas.fill_attr_apply(attr_map)
        return canvas

    def connect_signal(self, name, handler):
        """
        Shorthand to connect a signal to a handler function
        """
        urwid.connect_signal(self, name, handler)

    def forward_signal(self, name, new_widget, new_name, replace_args=False):
        """
        Shorthand to forward a signal to another widget.
        """

        def handler(*args):
            if replace_args:
                urwid.emit_signal(new_widget, new_name, new_widget)
            else:
                urwid.emit_signal(new_widget, new_name, *args)

        urwid.connect_signal(self, name, handler)

    def emit_signal(self, name):
        """
        Really, I just don't like how Widget._emit is named.
        """
        self._emit(name)


class RepeatedTextFill(urwid.Widget):
    """
    A widget that fills the screen with a single line of text.

    This is intended to be used like a SolidFill but with more than one
    character. Unicode characters with != 1 width are not supported, because
    urwid's text layout library make my head spin.
    """

    _sizing = frozenset([urwid.BOX])
    _selectable = False
    ignore_focus = True

    def __init__(self, fill_text, line_offset=-1):
        self.__super.__init__()
        self.fill_text = fill_text
        self.line_offset = line_offset

    def render(self, size, focus=False):
        max_col, max_row = size

        text_buffer = self.fill_text * (max_col // len(self.fill_text) + 2)

        text = []
        for i in range(max_row):
            offset = (self.line_offset * i) % len(self.fill_text)
            text.append(text_buffer[offset : offset + max_col])

        raw_text = [line.encode() for line in text]
        return urwid.TextCanvas(raw_text, maxcol=max_col, check_width=False)


class BoxShadow(urwid.WidgetDecoration, urwid.WidgetWrap):
    """
    Draw a half-width unicode box shadow behind the widget.

    Derived from urwid.LineBox, organic 100% cage-free.
    """

    def __init__(self, original_widget):
        top = urwid.Divider(" ")
        middle = urwid.Columns(
            [
                ("fixed", 1, urwid.SolidFill(" ")),
                original_widget,
                ("fixed", 1, urwid.Pile([("pack", urwid.Text("▖")), urwid.SolidFill("▌")])),
            ],
            box_columns=[0, 2],
            focus_column=1,
        )
        bottom = urwid.Columns(
            [
                ("fixed", 1, urwid.Text(" ")),
                ("fixed", 1, urwid.Text("▝")),
                urwid.Divider("▀"),
                ("fixed", 1, urwid.Text("▘")),
            ]
        )
        widget = urwid.Pile([("pack", top), middle, ("pack", bottom)])
        urwid.WidgetDecoration.__init__(self, original_widget)
        urwid.WidgetWrap.__init__(self, widget)


class SingleFocusPile(urwid.Pile):
    """
    The default file will only allow a single child widget to be in focus.

    This class extends Pile to allow all child widgets to be rendered as if
    they were in focus, regardless of which widget is actually selected.
    """

    def render(self, size, focus=False):
        maxcol = size[0]
        item_rows = None

        combinelist = []
        for i, (w, (f, height)) in enumerate(self.contents):
            item_focus = self.focus_item == w
            canv = None
            if f == urwid.widget.GIVEN:
                canv = w.render((maxcol, height), focus=focus)
            elif f == urwid.widget.PACK or len(size) == 1:
                canv = w.render((maxcol,), focus=focus)
            else:
                if item_rows is None:
                    item_rows = self.get_item_rows(size, focus)
                rows = item_rows[i]
                if rows > 0:
                    canv = w.render((maxcol, rows), focus=focus)
            if canv:
                combinelist.append((canv, i, item_focus))
        if not combinelist:
            return urwid.SolidCanvas(" ", size[0], (size[1:] + (0,))[0])

        out = urwid.CanvasCombine(combinelist)
        if len(size) == 2 and size[1] != out.rows():
            # flow/fixed widgets rendered too large/small
            out = urwid.CompositeCanvas(out)
            out.pad_trim_top_bottom(0, size[1] - out.rows())
        return out


class DataWidget(urwid.WidgetWrap):
    """
    Widget wrapper that additionally stores data representing the widget.
    """

    def __init__(self, widget, data=None):
        self.data = data
        super().__init__(widget)
