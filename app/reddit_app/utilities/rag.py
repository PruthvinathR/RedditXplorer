import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_core.runnables import RunnablePassthrough


load_dotenv(override=True)


def format_documents(documents):
    return "\n\n".join([doc.page_content for doc in documents])


if __name__ == "__main__":

    print("Retrieving...")

    embeddings = OpenAIEmbeddings(openai_api_key=os.environ["OPENAI_API_KEY"])
    llm = ChatOpenAI(model="gpt-4o-mini")

    query = "What is everyone saying about the about $300k loss."

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
    Use 3 sentences maximum and keep the answer concise. Finally say "Thank you for asking!"

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

    print(result.content)
