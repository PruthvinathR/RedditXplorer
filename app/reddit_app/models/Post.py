
class Post():
    post_id: str
    title: str
    upvotes: int | None = None
    username: str | None = None
    body: str | None = None
    comments: list[str] | None = None

    def __init__(self, post_id: str, title: str, upvotes: int | None = None, username: str | None = None, body: str | None = None, comments: list[str] | None = None):
        self.post_id = post_id
        self.title = title
        self.upvotes = upvotes
        self.username = username
        self.body = body
        self.comments = comments

    def to_dict(self):
        return {
            'post_id': self.post_id,
            'title': self.title,
            'upvotes': self.upvotes,
            'username': self.username,
            'body': self.body,
            'comments': self.comments
        }
