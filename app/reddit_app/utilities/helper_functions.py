# Standard library imports
import os

# Third-party imports
import praw
from langchain.text_splitter import CharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

# Local application imports
from app.reddit_app.models.Post import Post
from app.reddit_app.utilities.reddit_loader import RedditPostsLoader



def create_reddit_loader(subreddit, categories, number_posts):
    return RedditPostsLoader(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ["REDDIT_USER_AGENT"],
        categories=categories,
        number_posts=number_posts,
        mode="subreddit",
        search_queries=[subreddit]
    )


def create_post_summary_from_document(doc):
    return Post(
        post_id=doc.metadata["post_id"],
        title=doc.metadata["post_title"],
        upvotes=doc.metadata["post_score"],
        username=str(doc.metadata["post_author"])
    )


def create_post(**kwargs):
    return Post(
        post_id=kwargs.get("post_id", ''),
        title=kwargs.get("post_title", ''),
        upvotes=kwargs.get("post_score", 0),
        username=str(kwargs.get("post_author", '')),
        body=kwargs.get("post_body", ''),
        comments=kwargs.get("post_comments", [])
    )


def create_reddit_instance():
    return praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ["REDDIT_USER_AGENT"]
    )


def embed_post(post):
    embeddings = OpenAIEmbeddings(openai_api_key=os.environ["OPENAI_API_KEY"])
    # Step 1: Clear existing embeddings and store new embedding with metadata in Pinecone
    index = PineconeVectorStore.from_existing_index(index_name=os.environ["INDEX_NAME"], embedding=embeddings)
    # Check if there are existing embeddings before deleting
    if index._index.describe_index_stats()['total_vector_count'] > 0:
        index.delete(delete_all=True)  # Clear all existing vectors

    # Combine title, body, and comments
    content = f"Title: {post['title']}\nBody: {post['body']}\nComments: {' '.join(post['comments'])}"
    
    # Create a text splitter
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    # Split the content into chunks
    chunks = text_splitter.split_text(content)

    # Create Document objects for each chunk
    documents = [
        Document(
            page_content=chunk,
            metadata={
                'upvotes': post['upvotes'],
                'title': post['title']
            }
        ) for chunk in chunks
    ]
    
    # Add documents to the vector store
    index.add_documents(documents)

    return True
