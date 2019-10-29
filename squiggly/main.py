import urwid

from squiggly.api import Client
from squiggly.theme import palette
from squiggly.widgets import MainView


def main():
    # Add movement using h/j/k/l to default command map
    urwid.command_map["k"] = urwid.CURSOR_UP
    urwid.command_map["j"] = urwid.CURSOR_DOWN
    urwid.command_map["h"] = urwid.CURSOR_LEFT
    urwid.command_map["l"] = urwid.CURSOR_RIGHT

    client = Client()

    view = MainView()

    groups = client.list_groups()
    view.load_groups(groups)

    def on_select(widget, focus_data):
        data = client.list_topics(focus_data['name'])
        widget.load_topics(data)

    urwid.connect_signal(view, "select", on_select)

    event_loop = urwid.SelectEventLoop()
    main_loop = urwid.MainLoop(view, palette, event_loop=event_loop)

    try:
        main_loop.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
