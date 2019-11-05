import logging

import urwid

from squiggly.api import Client
from squiggly.theme import palette
from squiggly.views import SquigglyView


logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.DEBUG, filename='/tmp/squiggly.log')

    # Add movement using h/j/k/l to default command map
    urwid.command_map["k"] = urwid.CURSOR_UP
    urwid.command_map["j"] = urwid.CURSOR_DOWN
    urwid.command_map["h"] = urwid.CURSOR_LEFT
    urwid.command_map["l"] = urwid.CURSOR_RIGHT

    client = Client()

    view = SquigglyView()
    view.load_group_view(client.list_groups())

    def on_select_group(group_item):
        name = group_item.data["name"]
        data = client.list_topics(name)
        view.load_topic_view(data)

    def on_topic_more(topic_listbox):
        group = topic_listbox.data["group"]
        after = topic_listbox.data["last"]
        order = topic_listbox.data["order"]
        period = topic_listbox.data["period"]
        data = client.list_topics(group, after, order, period)
        topic_listbox.load_more(data)

    def on_topic_select(topic_listbox):
        topic_id = topic_listbox.data["id36"]
        data = client.get_topic(topic_id)
        view.load_comment_view(data)

    view.connect_signal("group_select", on_select_group)
    view.connect_signal("topic_more", on_topic_more)
    view.connect_signal("topic_select", on_topic_select)

    event_loop = urwid.SelectEventLoop()
    main_loop = urwid.MainLoop(view, palette, event_loop=event_loop)

    try:
        main_loop.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
