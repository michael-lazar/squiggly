import urwid

import squiggly


class KeyMap:

    def __init__(self):
        self.map = {}

    def __contains__(self, item):
        return self.map.__contains__(item)

    def __getitem__(self, item):
        return self.map.__getitem__(item)

    def register(self, *keys):
        def wrap_method(method):
            for key in keys:
                self.map[key] = method
            return method
        return wrap_method


class SquigglyBaseWidget(urwid.Widget):
    """
    Adds some helpful custom properties to base urwid Widget.

    default attributes:
        attr_name and focus_name define default theme groups that will be
        applied to the widget's canvas. This provides is a simple alternative
        to needing to wrap the widget with AttrMap() after creating it.

    keymap:
        The keyboard mapper is a lightweight decorator that can be used to bind
        a function to an individual keypress.
    """
    attr_name = None
    focus_name = None
    keymap = KeyMap()

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

    def keypress(self, size, key):
        if key in self.keymap:
            self.keymap[key](self)
        else:
            try:
                return super().keypress(size, key)
            except AttributeError:
                return key

    @classmethod
    def from_data(cls, data=None):
        return cls()


class ListItem(SquigglyBaseWidget, urwid.Text):
    _selectable = True
    keymap = KeyMap()

    def __init__(self, markup, data=None):
        self.data = data
        super().__init__(markup, wrap="clip")

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

    def __init__(self, list_walker):
        list_walker.set_focus_changed_callback(self.on_focus_change)
        super().__init__(list_walker)

    def on_focus_change(self, index):
        self._emit("on_focus_change", self.body[index].data)


class ContentView(urwid.Columns):
    def __init__(self, sidebar, infobox):
        super().__init__([(20, sidebar), infobox])
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

        markup = data["id36"]
        return cls(markup, data)


class GroupInfoBoxHeader(Header):
    attr_name = "group_infobox_header"

    @classmethod
    def from_data(cls, data=None):
        return cls("")


class TopicInfoBoxHeader(Header):
    attr_name = "topic_infobox_header"

    @classmethod
    def from_data(cls, data=None):
        return cls("")


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

        widgets = [
            ("pack", urwid.Text(data['title'] + "\n")),
            urwid.Filler(urwid.Text(data["content"] or data["link"]), valign="top"),
        ]
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


class MainView(SquigglyBaseWidget, urwid.Frame):
    keymap = KeyMap()
    signals = ["select"]

    def __init__(self):
        self.topics = TopicView.from_data()
        self.groups = GroupView.from_data()

        header = Header("squiggly")
        footer = Header(squiggly.__version__)
        super().__init__(self.groups, header, footer)

    def load_topics(self, data=None):
        self.topics = TopicView.from_data(data)
        self.body = self.topics

    def load_groups(self, data=None):
        self.groups = GroupView.from_data(data)
        self.body = self.groups

    @keymap.register("esc")
    def on_escape(self):
        if isinstance(self.body, TopicView):
            self.body = self.groups

    @keymap.register("enter")
    def on_enter(self):
        index = self.body.contents[0][0].body.body.focus
        data = self.body.contents[0][0].body.body[index].data
        self._emit("select", data)
