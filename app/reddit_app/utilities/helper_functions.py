# Standard library imports
import os

# Third-party imports
import praw
from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.text_splitter import CharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore

# Local application imports
from app.reddit_app.models.Post import Post
from app.reddit_app.utilities.reddit_loader import RedditPostsLoader



def create_reddit_loader(subreddit, categories, number_posts):
    """
    Create a RedditPostsLoader instance.

    This function initializes and returns a RedditPostsLoader object with the specified parameters.
    It uses environment variables for Reddit API credentials and takes subreddit, categories,
    and number of posts as inputs.

    Args:
        subreddit (str): The name of the subreddit to load posts from.
        categories (list): A list of categories to fetch posts from (e.g., ['hot', 'new']).
        number_posts (int): The number of posts to retrieve.

    Returns:
        RedditPostsLoader: An instance of RedditPostsLoader configured with the given parameters.
    """
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
    """
    Create a Post object from a document.

    This function takes a document and extracts relevant information to create a Post object.
    It uses the metadata from the document to set the post_id, title, upvotes, and username.

    Args:
        doc (Document): The document containing post information.

    Returns:
        Post: A Post object created from the document.
    """
    return Post(
        post_id=doc.metadata["post_id"],
        title=doc.metadata["post_title"],
        upvotes=doc.metadata["post_score"],
        username=str(doc.metadata["post_author"])
    )


def create_post(**kwargs):
    """
    Create a Post object from keyword arguments.

    This function creates a Post object using the provided keyword arguments.
    It sets the post_id, title, upvotes, username, body, and comments based on the provided values.

    Args:
        kwargs (dict): Keyword arguments containing post information.
    Returns:
        Post: A Post object created from the provided keyword arguments.
    """
    return Post(
        post_id=kwargs.get("post_id", ''),
        title=kwargs.get("post_title", ''),
        upvotes=kwargs.get("post_score", 0),
        username=str(kwargs.get("post_author", '')),
        body=kwargs.get("post_body", ''),
        comments=kwargs.get("post_comments", [])
    )


def create_reddit_instance():
    """
    Create a Reddit instance.

    This function initializes and returns a Reddit object with the specified parameters.
    It uses environment variables for Reddit API credentials.

    Returns:
        praw.Reddit: A Reddit object configured with the given parameters.  
    """
    return praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ["REDDIT_USER_AGENT"]
    )


def embed_post(post):
    """
    Embed a post into a vector store.

    This function takes a post object, combines its title, body, and comments,
    and then splits the content into chunks. Each chunk is converted into a Document object
    with metadata containing the upvotes and title. These documents are then added to a Pinecone vector store.

    Args:
        post (Post): The post object to be embedded.

    Returns:
        bool: True if the embedding process is successful, False otherwise.
    """ 

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


def format_documents(documents):
    """
    Format documents for retrieval.

    This function takes a list of documents and returns a single string
    by concatenating the page_content of each document.

    Args:
        documents (list): A list of Document objects.
    Returns:
        str: A single string containing the concatenated page_content of all documents.
    """
    return "\n\n".join([doc.page_content for doc in documents])


def reply_to_message(message):
    """
    Reply to a message using RAG.

    This function takes a message, retrieves relevant information from a vector store,
    and generates a response using a language model. It uses the OpenAI API for embeddings
    and the ChatOpenAI model for generating responses.

    Args:
        message (str): The message to be replied to.

    Returns:
        str: The generated response to the message.
    """ 

    embeddings = OpenAIEmbeddings(openai_api_key=os.environ["OPENAI_API_KEY"])
    llm = ChatOpenAI(model="gpt-4o-mini")

    query = message

    vectorstore = PineconeVectorStore(
        index_name=os.environ["INDEX_NAME"],
        embedding=embeddings,
    )

    retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
    combine_docs_chain = create_stuff_documents_chain(
        llm, prompt=retrieval_qa_chat_prompt
    )

    retrieval_chain = create_retrieval_chain(
        retriever=vectorstore.as_retriever(), combine_docs_chain=combine_docs_chain
    )

    result = retrieval_chain.invoke({"input": query})

    print(result["answer"])

    template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know. 
    Use 3 sentences maximum and keep the answer concise.

    {context}

    Question: {question}

    Helpful Answer:"""

    custom_rag_prompt = PromptTemplate.from_template(template)

    rag_chain = (
        {
            "context": vectorstore.as_retriever() | format_documents,
            "question": RunnablePassthrough(),
        }
        | custom_rag_prompt
        | llm
    )

    result = rag_chain.invoke(input=query)

    return result.content

