from datetime import datetime, timezone

import tildee


class Client:
    """
    Wrapper around tildes API endpoints.
    """
    DATE_FMT = '%Y-%m-%dT%H:%M:%SZ'

    # No current API endpoint to return these, so I copied them directly from
    # the website for now.
    GROUPS = [
        '~anime', '~arts', '~books', '~comp', '~creative', '~design', '~enviro',
        '~finance', '~food', '~games', '~games.game_design', '~games.tabletop',
        '~health', '~hobbies', '~humanities', '~lgbt', '~life', '~misc',
        '~movies', '~music', '~news', '~science', '~space', '~sports', '~talk',
        '~tech', '~test', '~tildes', '~tildes.official', '~tv',
    ]

    def __init__(self, username, password):
        self._client = tildee.TildesClient(username, password)

    def list_groups(self):
        for name in self.GROUPS:
            data = {}
            data['name'] = name
            yield data

    def list_topics(self, group):
        for topic in self._client.fetch_topic_listing(group):
            data = {}
            data['author'] = topic.author
            data['link'] = topic.link
            data['id36'] = topic.id36
            data['num_comments'] = topic.num_comments
            data['num_votes'] = topic.num_votes
            data['title'] = topic.title

            timestamp = datetime.strptime(topic.timestamp, self.DATE_FMT)
            timestamp = timestamp.replace(tzinfo=timezone.utc)
            data['timestamp'] = timestamp
            yield data
