from flask import jsonify, request
from app.reddit_app.utilities.helper_functions import create_reddit_loader, create_reddit_instance, create_post_summary_from_document, create_post, embed_post, reply_to_message
from flask import Blueprint


post_controller_bp = Blueprint('post_controller', __name__, url_prefix='/reddit')

@post_controller_bp.route('/posts', methods=['GET'])
def get_reddit_posts():
    subreddit = request.args.get('subreddit', 'wallstreetbets')
    categories = request.args.get('categories', 'hot').split(',')
    number_posts = int(request.args.get('limit', 10))

    loader = create_reddit_loader(subreddit, categories, number_posts)
    documents = loader.load()
    print(f"Loaded {len(documents)} documents")

    posts = [create_post_summary_from_document(doc).to_dict() for doc in documents]
    
    return jsonify(posts)


@post_controller_bp.route('/post', methods=['GET'])
def get_reddit_post_by_id():
    post_id = request.args.get('post_id')
    reddit = create_reddit_instance()
    
    submission = reddit.submission(id=post_id)
    
    comments = [comment.body for comment in submission.comments.list() if hasattr(comment, 'body')]
    body = submission.selftext
    post = {'post_id': post_id, 'post_title': submission.title, 'post_body': body, 'post_comments': comments}
    post = create_post(**post)
    
    embed_post(post.to_dict())

    return jsonify(post.to_dict())


@post_controller_bp.route('/chat', methods=['POST'])
def chat_with_post():
    data = request.json
    post_id = data.get('post_id')
    message = data.get('message')
    chat_history = data.get('chat_history', [])
    response = reply_to_message(message, chat_history)
    return jsonify({'response': response})
