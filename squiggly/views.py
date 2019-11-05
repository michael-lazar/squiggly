import urwid

from squiggly import widgets


class Background(widgets.EnhancedWidget, widgets.RepeatedTextFill):
    attr_name = "background"

    def __init__(self):
        super().__init__(" ")


class Header(widgets.EnhancedWidget, urwid.Text):
    attr_name = "header"

    def __init__(self, markdown):
        super().__init__(markdown, wrap="clip")


class Footer(widgets.EnhancedWidget, urwid.Text):
    attr_name = "footer"

    def __init__(self, markdown):
        super().__init__(markdown, wrap="clip")


class ListItem(widgets.EnhancedWidget, widgets.DataWidget):
    signals = ["select"]

    def selectable(self):
        return True

    def keypress(self, size, key):
        if key in ("enter", "right"):
            self.emit_signal("select")
        else:
            return key


class GroupItem(ListItem):

    def __init__(self, data):
        name = urwid.Padding(urwid.Text(data['name'], wrap="clip"), left=0)
        name = urwid.AttrMap(name, "group_item_name")
        desc = urwid.Padding(urwid.Text(data["desc"]), left=4)
        desc = urwid.AttrMap(desc, "group_item_desc")
        widget = widgets.SingleFocusPile([("pack", name), ("pack", desc)])
        widget = urwid.AttrMap(widget, "group_item_inner")
        widget = widgets.BoxShadow(widget)
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


class ListBox(widgets.EnhancedWidget, widgets.DataWidget):
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
    attr_name = "group_listbox"
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
        return items


class SquigglyView(widgets.EnhancedWidget, urwid.WidgetWrap):
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
        self.foreground = widgets.BoxShadow(self.frame)
        self.background = Background()
        self.overlay = urwid.Overlay(
            top_w=self.foreground,
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
