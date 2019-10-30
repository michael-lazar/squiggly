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

    data = client.list_groups()
    view.load_groups_page(data)

    def on_select_group(widget):
        data = client.list_topics(widget.focus_data['name'])
        widget.load_topics_page(data)

    urwid.connect_signal(view, "select_group", on_select_group)

    event_loop = urwid.SelectEventLoop()
    main_loop = urwid.MainLoop(view, palette, event_loop=event_loop)

    try:
        main_loop.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
