from concurrent.futures import ThreadPoolExecutor

import urwid

import squiggly.widgets
import squiggly.api
import squiggly.theme


class Application:

    def __init__(self):

        self.client = squiggly.api.Client()

        groups = self.client.list_groups()
        groups_frame = squiggly.widgets.GroupsFrame()
        groups_frame.body.load_content(groups)

        topics = self.client.list_topics('~news')
        topics_frame = squiggly.widgets.TopicsFrame()
        topics_frame.body.load_content(topics)

        event_loop = urwid.SelectEventLoop()

        @squiggly.widgets.apply_signal(groups_frame, "focus_changed")
        def on_change(*args):
            name = self.view.contents[0][0].body.focus.original_widget.text
            topics = self.client.list_topics(name)
            topics_frame = squiggly.widgets.TopicsFrame()
            topics_frame.body.load_content(topics)

            contents = self.view.contents
            contents[1] = (topics_frame, contents[1][1])
            self.view.contents = contents

        sidebar = squiggly.widgets.Sidebar(event_loop=event_loop)

        self.view = urwid.Columns(
            [
                (20, groups_frame),
                topics_frame,
                ('pack', sidebar),
            ]
        )
        self.loop = urwid.MainLoop(self.view, squiggly.theme.palette, event_loop=event_loop)

    @classmethod
    def run(cls):

        # Add movement using h/j/k/l to default command map
        urwid.command_map['k'] = urwid.CURSOR_UP
        urwid.command_map['j'] = urwid.CURSOR_DOWN
        urwid.command_map['h'] = urwid.CURSOR_LEFT
        urwid.command_map['l'] = urwid.CURSOR_RIGHT

        application = cls()

        with ThreadPoolExecutor(max_workers=1) as executor:
            application.loop.run()


main = Application.run


if __name__ == '__main__':
    Application.run()
