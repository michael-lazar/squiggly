"""
Widget Cheatsheet:

http://urwid.org/manual/widgets.html

A container widget contains other widgets, and is responsible for the size and
position of their child widgets. They must also determine which (if any) of
their child widgets is currently in-focus.

How a widget's size is determined:

    Box widgets are given the exact number of rows and columns to fill. The
    topmost widgets is always a box widget and it gets it's size from the
    screen.

    Flow widgets are given a number of available columns from their parent, and
    then they determine the number of rows necessary to display their content.

    Fixed widgets are not given either the number of available rows or columns.
    They calculate the exact size that they need to display.

Decoration widgets alter the attributes or appearance of a single widget. The
widget that they wrap is available using the `original_widget` property.
"""
import urwid


def add_style_classmethod(attr_map, focus_map=None):
    """
    Create a helper classmethod that can be used to create an instance of a
    widget with a pre-defined attribute map.
    """
    def constructor_method(widget_class, *args, **kwargs):
        widget = widget_class(*args, **kwargs)
        return urwid.AttrMap(widget, attr_map, focus_map)
    return classmethod(constructor_method)


def apply_signal(source, signal):
    """
    I really enjoy decorators...
    """
    def wrapper(sink):
        urwid.connect_signal(source, signal, sink)
        return sink
    return wrapper


class SelectableText(urwid.Text):
    _selectable = True

    def keypress(self, size, key):
        return key


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
            text.append(text_buffer[offset:offset+max_col])

        raw_text = [line.encode() for line in text]
        return urwid.TextCanvas(raw_text, maxcol=max_col, check_width=False)


class AnimatedMixin:
    """
    Enables animated transitions for widgets using the urwid event loop.
    """
    def __init__(self, event_loop, *args, **kwargs):
        self.event_loop = event_loop
        self.___lock = False
        super().__init__(*args, **kwargs)

    def play(self):
        if self.___lock:
            return

        def render_frame():
            delay = self.next_frame()
            if delay is None:
                self.___lock = False
            else:
                self.event_loop.alarm(delay, render_frame)

        self.___lock = True
        self.event_loop.alarm(0, render_frame)

    def next_frame(self):
        raise NotImplementedError


class Sidebar(AnimatedMixin, urwid.WidgetWrap):

    def __init__(self, event_loop):
        self.hidden = urwid.AttrMap(urwid.Filler(urwid.Text('~')), 'sidebar')
        self.active = urwid.AttrMap(urwid.Filler(urwid.Text('Hello!')), 'sidebar')

        self.width = 1
        self.is_active = False
        super().__init__(event_loop, self.hidden)

    def next_frame(self):
        if self.is_active and self.width < 8:
            self.width += 1
            self._invalidate()
            return 1 / 30
        elif not self.is_active and self.width > 1:
            self.width -= 1
            self._invalidate()
            return 1 / 30

    def keypress(self, size, key):
        if self.is_active:
            self.is_active = False
            self._w = self.hidden
            self.play()
        else:
            self.is_active = True
            self._w = self.active
            self.play()

    def selectable(self):
        return True

    def pack(self, size=None, focus=False):
        """
        Even though this is a wrapper for a box widget, pack() is used by the
        Columns container to figure out how wide to make the widget. The
        calculated height doesn't matter, so we're returning None.
        """
        maxcol, = size
        return min(maxcol, self.width), None


class GroupsListBox(urwid.ListBox):
    """
    A listbox widget with all of the tildes groups, e.g. ~hobbies, ~games.
    """

    signals = [
        "focus_changed"  # Focus changed
    ]

    def focus_changed(self, index):
        """Called when the list focus switches to a new element"""
        self._emit("focus_changed", index)

    def load_content(self, groups):
        body = []
        for data in groups:
            text_widget = SelectableText(data['name'])
            text_widget = urwid.AttrMap(text_widget, 'groups_normal', 'groups_selected')
            body.append(text_widget)
        self.body[:] = body

    def __init__(self):
        list_walker = urwid.SimpleFocusListWalker([])
        list_walker.set_focus_changed_callback(self.focus_changed)
        super().__init__(list_walker)


class GroupsFrame(urwid.Frame):

    signals = [
        "focus_changed"  # Focus changed
    ]

    def focus_changed(self, *args):
        """Called when the list focus switches to a new element"""
        self._emit("focus_changed", *args)

    def __init__(self):
        body = GroupsListBox()
        urwid.connect_signal(body, 'focus_changed', self.focus_changed)
        header = urwid.AttrMap(urwid.Text('Groups'), 'groups_header')
        super().__init__(body, header)


class TopicsListBox(urwid.ListBox):
    """
    A listbox widget with all of the tildes topics for a group.
    """

    def load_content(self, topics):
        body = []
        for data in topics:
            text_widget = SelectableText(data['title'])
            text_widget = urwid.AttrMap(text_widget, 'topics_normal', 'topics_selected')
            body.append(text_widget)
        self.body[:] = body

    def __init__(self):
        super().__init__(urwid.SimpleFocusListWalker([]))


class TopicsFrame(urwid.Frame):

    def __init__(self):
        body = TopicsListBox()
        header = urwid.AttrMap(urwid.Text('Topics'), 'topics_header')
        super().__init__(body, header)
