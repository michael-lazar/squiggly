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


def rainbow_background():
    while True:
        for i in range(1, 7):
            yield urwid.AttrSpec(f"h{i},standout", "default"), urwid.AttrSpec(f"h{i}", "default")


rainbow_background_gen = rainbow_background()


class SquigglyBaseWidget(urwid.Widget):
    attr_name = None
    focus_name = None

    def render(self, size, focus=False):
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

    @classmethod
    def from_data(cls, data=None):
        return cls()


class ListItem(SquigglyBaseWidget, urwid.Text):
    _selectable = True

    signals = ["select"]

    def __init__(self, markup, data=None):
        self.data = data
        super().__init__(markup, wrap="clip")

    def keypress(self, size, key):
        if key == "enter":
            self._emit("select")
        else:
            return key

    def text_width(self):
        """
        The number of columns required for the text to fit on a single line.
        """
        return self.pack()[0]


class Header(SquigglyBaseWidget, urwid.Text):
    def __init__(self, markdown):
        super().__init__(markdown, wrap="clip")


class InfoBox(SquigglyBaseWidget, urwid.Pile):
    pass


class Sidebar(SquigglyBaseWidget, urwid.ListBox):
    signals = ["on_focus_change"]

    width_default = 10

    def __init__(self, list_walker):
        width_gen = (x.text_width() for x in list_walker)
        width = max(width_gen, default=self.width_default)
        self.width = width

        list_walker.set_focus_changed_callback(self.on_focus_change)
        super().__init__(list_walker)

    def on_focus_change(self, index):
        self._emit("on_focus_change", self.body[index].data)


class ContentView(urwid.Columns):
    def __init__(self, sidebar, infobox):
        super().__init__([(sidebar.body.width, sidebar), infobox])
        urwid.connect_signal(sidebar.body, "on_focus_change", self.set_infobox)

    def set_infobox(self, _, data):
        infobox = self.build_infobox(data)

        # Swap out the infobox while preserving the column display options
        _, options = self.contents[1]
        self.contents[1] = (infobox, options)

    def build_infobox(self, data):
        raise NotImplementedError


class GroupListItem(ListItem):
    attr_name = "group_list_item_normal"
    focus_name = "group_list_item_selected"

    @classmethod
    def from_data(cls, data=None):
        if not data:
            cls("", data)

        markup = data["name"]
        return cls(markup, data)


class TopicListItem(ListItem):
    attr_name = "topic_list_item_normal"
    focus_name = "topic_list_item_selected"

    @classmethod
    def from_data(cls, data=None):
        if not data:
            cls("", data)

        markup = data["timestamp"].isoformat(" ")
        return cls(markup, data)


class GroupInfoBoxHeader(Header):
    attr_name = "group_infobox_header"

    @classmethod
    def from_data(cls, data=None):
        if not data:
            return cls("")

        return cls(data["name"])


class TopicInfoBoxHeader(Header):
    attr_name = "topic_infobox_header"

    @classmethod
    def from_data(cls, data=None):
        if not data:
            return cls("")

        return cls(data["title"])


class GroupSidebarHeader(Header):
    attr_name = "group_sidebar_header"

    def __init__(self):
        super().__init__("Groups")


class TopicSidebarHeader(Header):
    attr_name = "topic_sidebar_header"

    def __init__(self):
        super().__init__("Topics")


class GroupInfoBox(InfoBox):
    attr_name = "group_infobox_normal"
    focus_name = "group_infobox_selected"

    @classmethod
    def from_data(cls, data=None):
        if not data:
            return cls([])

        widgets = [urwid.Filler(urwid.Text(data["desc"]), valign="top")]
        return cls(widgets)


class TopicInfoBox(InfoBox):
    attr_name = "topic_infobox_normal"
    focus_name = "topic_infobox_selected"

    @classmethod
    def from_data(cls, data=None):
        if not data:
            return cls([])

        body = data["content"] or data["link"]
        widgets = [urwid.Filler(urwid.Text(body), valign="top")]
        return cls(widgets)


class GroupSidebar(Sidebar):
    attr_name = "group_sidebar_normal"
    focus_name = "group_sidebar_selected"

    @classmethod
    def from_data(cls, data=None):
        data = data or []

        list_items = []
        for group_data in data:
            list_item = GroupListItem.from_data(group_data)
            list_items.append(list_item)

        list_walker = urwid.SimpleFocusListWalker(list_items)
        return cls(list_walker)


class TopicSidebar(Sidebar):
    attr_name = "topic_sidebar_normal"
    focus_name = "topic_sidebar_selected"

    @classmethod
    def from_data(cls, data=None):
        data = data or []

        list_items = []
        for group_data in data:
            list_item = TopicListItem.from_data(group_data)
            list_items.append(list_item)

        list_walker = urwid.SimpleFocusListWalker(list_items)
        return cls(list_walker)


class GroupView(ContentView):
    @classmethod
    def build_sidebar(cls, data=None):
        body = GroupSidebar.from_data(data)
        header = GroupSidebarHeader.from_data(data)
        return urwid.Frame(body, header)

    @classmethod
    def build_infobox(cls, data=None):
        body = GroupInfoBox.from_data(data)
        header = GroupInfoBoxHeader.from_data(data)
        return urwid.Frame(body, header)

    @classmethod
    def from_data(cls, data=None):
        sidebar = cls.build_sidebar(data)
        infobox = cls.build_infobox(data[0] if data else None)
        return cls(sidebar, infobox)


class TopicView(ContentView):
    @classmethod
    def build_sidebar(cls, data=None):
        body = TopicSidebar.from_data(data)
        header = TopicSidebarHeader.from_data(data)
        return urwid.Frame(body, header)

    @classmethod
    def build_infobox(cls, data=None):
        body = TopicInfoBox.from_data(data)
        header = TopicInfoBoxHeader.from_data(data)
        return urwid.Frame(body, header)

    @classmethod
    def from_data(cls, data=None):
        sidebar = cls.build_sidebar(data)
        infobox = cls.build_infobox(data[0] if data else None)
        return cls(sidebar, infobox)
