import urwid


class KeyMap:
    """
    A light interface around urwid's Widget.keypress() that uses a decorator
    function to register a method with one or more keyboard keys.
    """
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
    Extend the urwid base Widget with some custom behavior.
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
            return  # Return `None` to indicate that the key was handled

        try:
            return super().keypress(size, key)
        except AttributeError:
            return key


class DataFrame:
    _selectable = True

    def __init__(self, *args, data=None, **kwargs):
        self.data = data
        super().__init__(*args, **kwargs)

    @classmethod
    def from_data(cls, data):
        raise NotImplementedError


class BaseText(SquigglyBaseWidget, urwid.Text):
    pass


class BaseFrame(SquigglyBaseWidget, urwid.Frame):
    pass


class BaseListBox(SquigglyBaseWidget, urwid.ListBox):
    signals = [
        "change_focus",  # A new item has been selected
    ]

    def __init__(self, list_walker):
        list_walker.set_focus_changed_callback(self.on_focus_change)
        super().__init__(list_walker)

    def on_focus_change(self, index):
        self._emit("change_focus", self.body[index])


class Header(BaseText):
    attr_name = "header"

    def __init__(self, markdown):
        super().__init__(markdown, wrap="clip")


class Footer(BaseText):
    attr_name = "footer"

    def __init__(self, markdown):
        super().__init__(markdown, wrap="clip")


class GroupItem(DataFrame, BaseText):
    attr_name = "group_item"
    focus_name = "group_item_focus"

    @classmethod
    def from_data(cls, data):
        markup = [
            data['name'],
            "\n",
            data["desc"],
        ]
        return cls(markup, data=data)


class TopicItem(DataFrame, BaseText):
    attr_name = "topic_item"
    focus_name = "topic_item_focus"

    @classmethod
    def from_data(cls, data):
        markup = [
            data["title"],
        ]
        return cls(markup, data=data)


class CommentItem(DataFrame, BaseText):

    @classmethod
    def from_data(cls, data):
        return cls(None, data=data)


class PartialTopicItem(DataFrame, BaseText):

    @classmethod
    def from_data(cls, data):
        return cls(None, data=data)


class PartialCommentItem(DataFrame, BaseText):

    @classmethod
    def from_data(cls, data):
        return cls(None, data=data)


class GroupListBox(DataFrame, BaseListBox):

    @classmethod
    def from_data(cls, data_list):
        items = []
        for index, data in enumerate(data_list, start=1):
            data["index"] = index
            item = GroupItem.from_data(data)
            items.append(item)
            if index < len(data_list):
                items.append(urwid.Divider())

        list_walker = urwid.SimpleFocusListWalker(items)
        return cls(list_walker, data=data_list)


class TopicListBox(DataFrame, BaseListBox):

    @classmethod
    def from_data(cls, data_list):
        items = []
        for index, data in enumerate(data_list, start=1):
            data["index"] = index
            item = TopicItem.from_data(data)
            items.append(item)
            if index < len(data_list):
                items.append(urwid.Divider())

        list_walker = urwid.SimpleFocusListWalker(items)
        return cls(list_walker, data=data_list)


class MainView(BaseFrame):
    keymap = KeyMap()
    signals = [
        "select_group"
    ]

    def __init__(self):
        self.group_view = GroupListBox.from_data([])
        self.topic_view = TopicListBox.from_data([])

        header = Header("Header")
        footer = Footer("Footer")
        super().__init__(self.group_view, header, footer)

    def load_topics_page(self, data_list):
        self.body = self.topic_view = TopicListBox.from_data(data_list)

    def load_groups_page(self, data_list):
        self.body = self.group_view = GroupListBox.from_data(data_list)

    @property
    def focus_data(self):
        if self.body.focus:
            return self.body.focus.data

    @keymap.register("esc")
    def on_escape(self):
        if self.body == self.topic_view:
            self.body = self.group_view

    @keymap.register("enter")
    def on_enter(self):
        if self.body == self.group_view:
            self._emit("select_group")
