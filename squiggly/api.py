from datetime import datetime, timezone

from tildee import TildesClient
from html2text import html2text


class Client:

    DATETIME_FMT = "%Y-%m-%dT%H:%M:%SZ"

    def __init__(self):
        self._client = TildesClient(user_agent="michael-lazar/squiggly")

    def _parse_group(self, group):
        data = {}
        data["desc"] = group.desc
        data["name"] = group.name
        data["num_subscribers"] = group.num_subscribers
        data["subscribed"] = group.subscribed
        return data

    def _parse_topic(self, topic):
        data = {}
        data["author"] = topic.author
        data["group"] = topic.group
        data["id36"] = topic.id36
        data["link"] = topic.link
        data["num_comments"] = topic.num_comments
        data["num_votes"] = topic.num_votes
        data["title"] = topic.title

        timestamp = datetime.strptime(topic.timestamp, self.DATETIME_FMT)
        timestamp.replace(tzinfo=timezone.utc)
        data["timestamp"] = timestamp

        data["content"] = html2text(topic.content_html) if topic.content_html else ""
        return data

    def list_groups(self):
        groups = self._client.fetch_groups()
        data = [self._parse_group(group) for group in groups]
        return data

    def list_topics(self, path=""):
        topics = self._client.fetch_topic_listing(path)
        data = [self._parse_topic(topic) for topic in topics]
        return data
