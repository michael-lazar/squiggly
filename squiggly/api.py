from datetime import datetime, timezone

from tildee import TildesClient


class Client:

    def __init__(self):
        self._client = TildesClient(user_agent="michael-lazar/squiggly", ratelimit=0)

    def _decode_timestamp(self, timestamp_str):
        if timestamp_str is None:
            return None

        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")
        timestamp.replace(tzinfo=timezone.utc)
        return timestamp

    def _flatten_comment_tree(self, comments, level=0, parent_id=None):
        for c in comments:
            c.level = level
            c.parent_id = parent_id

        flattened_comments = []
        stack = comments[::-1]
        while stack:
            comment = stack.pop()
            for child in comment.children:
                child.level = comment.level + 1
                child.parent_id = comment.id36
                stack.append(child)
            flattened_comments.append(comment)
        return flattened_comments

    def _parse_group(self, group):
        data = {}
        data["type"] = "group"
        data["desc"] = group.desc
        data["name"] = f"~{group.name}"
        data["num_subscribers"] = group.num_subscribers
        data["subscribed"] = group.subscribed
        return data

    def _parse_partial_topic(self, topic):
        data = {}
        data["type"] = "partial_topic"
        data["author"] = topic.author
        data["group"] = topic.group
        data["id36"] = topic.id36
        data["link"] = topic.link
        data["num_comments"] = topic.num_comments
        data["num_votes"] = topic.num_votes
        data["title"] = topic.title
        data["content"] = topic.content
        data["timestamp"] = self._decode_timestamp(topic.timestamp)
        return data

    def _parse_topic(self, topic):
        comments = self._flatten_comment_tree(topic.comments)

        data = {}
        data["type"] = "topic"
        data["author"] = topic.author
        data["group"] = topic.group
        data["id36"] = topic.id36
        data["link"] = topic.link
        data["num_comments"] = int(topic.num_comments)
        data["num_votes"] = topic.num_votes
        data["title"] = topic.title
        data["content"] = topic.content
        data["is_locked"] = topic.is_locked
        data["tags"] = topic.tags
        data["timestamp"] = self._decode_timestamp(topic.timestamp)
        data["comments"] = [self._parse_comment(comment) for comment in comments]
        return data

    def _parse_comment(self, comment):
        data = {}
        data["type"] = "comment"
        data["level"] = comment.level
        data["parent_id"] = comment.parent_id
        data["author"] = comment.author
        data["content"] = comment.content.strip()
        data["id36"] = comment.id36
        data["status"] = comment.status.name
        data["timestamp"] = self._decode_timestamp(comment.timestamp)
        return data

    def list_groups(self):
        groups = self._client.fetch_groups()

        data = {}
        data["groups"] = [self._parse_group(group) for group in groups]
        return data

    def list_topics(self, group="", after="", order="", period=""):
        topics = self._client.fetch_topic_listing(group, after, order, period, per_page=5)

        data = {}
        data["group"] = group
        data["after"] = after
        data["order"] = order
        data["period"] = period
        data["last"] = topics[-1].id36 if topics else None
        data["topics"] = [self._parse_partial_topic(topic) for topic in topics]
        return data

    def get_topic(self, topic_id):
        topic = self._client.fetch_topic(topic_id)
        return self._parse_topic(topic)
