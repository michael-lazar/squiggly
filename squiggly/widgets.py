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
import urwid


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


class WTFPile(urwid.Pile):

    @property
    def focus_item(self):
        class Mock:
            def __eq__(self, other):
                return True
        return Mock()


class Background(EnhancedWidget, RepeatedTextFill):
    attr_name = "background"

    def __init__(self):
        super().__init__(" ")


class DataWidget(urwid.WidgetWrap):
    """
    Widget wrapper that additionally stores data representing the widget.
    """
    def __init__(self, widget, data=None):
        self.data = data
        super().__init__(widget)


class Header(EnhancedWidget, urwid.Text):
    attr_name = "header"

    def __init__(self, markdown):
        super().__init__(markdown, wrap="clip")


class Footer(EnhancedWidget, urwid.Text):
    attr_name = "footer"

    def __init__(self, markdown):
        super().__init__(markdown, wrap="clip")


class ListItem(EnhancedWidget, DataWidget):
    signals = ["select"]

    def selectable(self):
        return True

    def keypress(self, size, key):
        if key in ("enter", "right"):
            self.emit_signal("select")
        else:
            return key


class GroupItem(ListItem):
    attr_name = "group_item"
    focus_name = "group_item_focus"

    def __init__(self, data):
        name = urwid.Text(data['name'], wrap="clip")
        name = urwid.AttrMap(name, "group_item_name", "group_item_focus")
        desc = urwid.Padding(urwid.Text(data["desc"]), left=4)
        desc = urwid.AttrMap(desc, "group_item_desc", "group_item_focus")
        widget = WTFPile([("pack", name), ("pack", desc)])
        super().__init__(widget, data)


class TopicItem(ListItem):
    attr_name = "topic_item"
    focus_name = "topic_item_focus"

    def __init__(self, data):
        widget = urwid.Text([data["title"]])
        super().__init__(widget, data)


class CommentItem(ListItem):
    attr_name = "comment_item"
    focus_name = "comment_item_focus"

    def __init__(self, data):
        widget = urwid.Text([data['content'] or ''])
        super().__init__(widget, data)


class LoadItem(ListItem):
    attr_name = "load_item"
    focus_name = "load_item_focus"

    def __init__(self):
        widget = urwid.Text("Load...")
        super().__init__(widget)


class ListBox(EnhancedWidget, DataWidget):
    signals = [
        "close",
    ]

    def keypress(self, size, key):
        if key == "left":
            self.emit_signal("close")
        else:
            return super().keypress(size, key)


class TopicListBox(ListBox):
    signals = [
        "select",
        "more",
    ]

    def __init__(self, data):
        topics = data.setdefault("topics", [])
        list_items = self.build_list_items(topics)
        widget = urwid.ListBox(urwid.SimpleFocusListWalker(list_items))
        super().__init__(widget, data)

    def build_list_items(self, topics):
        items = []
        for data in topics:
            topic_item = TopicItem(data)
            topic_item.forward_signal("select", self, "select")
            items.append(topic_item)
            items.append(urwid.Divider())

        if topics:
            load_item = LoadItem()
            load_item.forward_signal("select", self, "more", replace_args=True)
            items.append(load_item)

        return items

    def load_more(self, data):
        topics = data.setdefault("topics", [])
        self._w.body[-1:] = self.build_list_items(topics)
        self.data["last"] = topics[-1]["id36"] if topics else None


class GroupListBox(ListBox):
    signals = [
        "select",
    ]

    def __init__(self, data):
        groups = data.setdefault("groups", [])
        list_items = self.build_list_items(groups)
        widget = urwid.ListBox(urwid.SimpleFocusListWalker(list_items))
        super().__init__(widget, data)

    def build_list_items(self, groups):
        items = []
        for data in groups:
            group_item = GroupItem(data)
            group_item.forward_signal("select", self, "select")
            items.append(group_item)
            items.append(urwid.Divider())
        return items


class CommentListBox(ListBox):
    signals = [
        "select",
    ]

    def __init__(self, data):
        comments = data.setdefault("comments", [])
        list_items = self.build_list_items(comments)
        widget = urwid.ListBox(urwid.SimpleFocusListWalker(list_items))
        super().__init__(widget, data)

    def build_list_items(self, comments):
        items = []
        for data in comments:
            comment_item = CommentItem(data)
            comment_item.forward_signal("select", self, "select")
            items.append(comment_item)
            items.append(urwid.Divider())
        return items


class SquigglyView(EnhancedWidget, urwid.WidgetWrap):
    signals = [
        "group_select",
        "topic_select",
        "topic_more",
        "topic_close",
        "comment_close",
    ]

    def __init__(self):
        self.header = Header("Header")
        self.footer = Footer("Footer")
        self.topic_view = TopicListBox({})
        self.group_view = GroupListBox({})
        self.comment_view = CommentListBox({})
        self.frame = urwid.Frame(self.group_view, self.header, self.footer)
        self.background = Background()
        self.overlay = urwid.Overlay(
            top_w=self.frame,
            bottom_w=self.background,
            align="center",
            width=120,
            valign="middle",
            height=100,
        )
        super().__init__(self.overlay)

    @property
    def topic_view(self):
        return self._topic_view

    @topic_view.setter
    def topic_view(self, topic_listbox):
        topic_listbox.forward_signal("select", self, "topic_select")
        topic_listbox.forward_signal("more", self, "topic_more")
        topic_listbox.connect_signal("close", self.on_topic_close)
        self._topic_view = topic_listbox

    @property
    def group_view(self):
        return self._group_view

    @group_view.setter
    def group_view(self, group_listbox):
        group_listbox.forward_signal("select", self, "group_select")
        self._group_view = group_listbox

    @property
    def comment_view(self):
        return self._comment_view

    @comment_view.setter
    def comment_view(self, comment_listbox):
        comment_listbox.connect_signal("close", self.on_comment_close)
        self._comment_view = comment_listbox

    def load_topic_view(self, data):
        self.frame.body = self.topic_view = TopicListBox(data)

    def load_group_view(self, data):
        self.frame.body = self.group_view = GroupListBox(data)

    def load_comment_view(self, data):
        self.frame.body = self.comment_view = CommentListBox(data)

    def on_topic_close(self, *_):
        self.frame.body = self.group_view

    def on_comment_close(self, *_):
        self.frame.body = self.topic_view
