import urwid

from squiggly.api import Client
from squiggly.theme import palette
from squiggly.widgets import GroupView, TopicView


def main():
    # Add movement using h/j/k/l to default command map
    urwid.command_map["k"] = urwid.CURSOR_UP
    urwid.command_map["j"] = urwid.CURSOR_DOWN
    urwid.command_map["h"] = urwid.CURSOR_LEFT
    urwid.command_map["l"] = urwid.CURSOR_RIGHT

    client = Client()

    group_data_list = client.list_groups()
    view = GroupView.from_data(group_data_list)

    # topic_data_list = client.list_topics()
    # view = TopicView.from_data(topic_data_list)

    event_loop = urwid.SelectEventLoop()
    main_loop = urwid.MainLoop(view, palette, event_loop=event_loop)
    main_loop.run()


if __name__ == "__main__":
    main()
