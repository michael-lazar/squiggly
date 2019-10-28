from datetime import datetime, timezone

import tildee
from lxml import etree
from html2text import html2text


class AnonymousTildesClient(tildee.TildesClient):

    assert tildee.__version__ == '0.5.0'

    def _login(self, password, totp_code=None):
        self._csrf_token = None
        self._cookies = None


class Client:

    DATETIME_FMT = '%Y-%m-%dT%H:%M:%SZ'

    def __init__(self):
        self._client = AnonymousTildesClient('mozz', '')

    def _parse_group(self, group):
        data = {}
        data['desc'] = group.desc
        data['name'] = group.name
        data['num_subscribers'] = group.num_subscribers
        data['subscribed'] = group.subscribed
        return data

    def _parse_topic(self, topic):
        data = {}
        data['author'] = topic.author
        data['group'] = topic.group
        data['id36'] = topic.id36
        data['link'] = topic.link
        data['num_comments'] = topic.num_comments
        data['num_votes'] = topic.num_votes
        data['title'] = topic.title

        timestamp = datetime.strptime(topic.timestamp, self.DATETIME_FMT)
        timestamp.replace(tzinfo=timezone.utc)
        data['timestamp'] = timestamp

        data['content'] = ""
        if topic.content_html:
            tree = topic._tree.cssselect(".topic-text-excerpt")[0]
            etree.strip_elements(tree, "summary")
            content_html = etree.tostring(tree).decode()
            data['content'] = html2text(content_html)

        return data

    def list_groups(self):
        groups = self._client.fetch_groups()
        data = [self._parse_group(group) for group in groups]
        return data

    def list_topics(self, path=''):
        topics = self._client.fetch_topic_listing(path)
        data = [self._parse_topic(topic) for topic in topics]
        return data
