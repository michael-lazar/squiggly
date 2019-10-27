import urwid

from squiggly.api import MockClient
from squiggly.widgets import GroupView
from squiggly.theme import palette


def main():
    # Add movement using h/j/k/l to default command map
    urwid.command_map['k'] = urwid.CURSOR_UP
    urwid.command_map['j'] = urwid.CURSOR_DOWN
    urwid.command_map['h'] = urwid.CURSOR_LEFT
    urwid.command_map['l'] = urwid.CURSOR_RIGHT

    client = MockClient()

    group_data_list = client.list_groups()
    view = GroupView.from_data(group_data_list)

    event_loop = urwid.SelectEventLoop()
    main_loop = urwid.MainLoop(view, palette, event_loop=event_loop)
    main_loop.run()


if __name__ == '__main__':
    main()
