import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.tools.retriever import create_retriever_tool
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("Did not find openai_api_key, please add an environment variable `OPENAI_API_KEY` which contains it, or pass `openai_api_key` as a named parameter.")

def create_retriever_tool_from_directory( k: int):
    # Create a retriever tool from embeddings in the specified directory.
    base_directory = os.path.join('stored_embeds')

    embeddings = load_embeddings(base_directory)
    retriever = embeddings.as_retriever(search_type='similarity', search_kwargs={'k': k})
    retriever_tool = create_retriever_tool(
    retriever,
    "retriever_name",
    "This retriever tool uses embeddings from stored documents to find similar content based on semantic similarity. It is particularly effective for summarizing web pages and finding related information.",
    )

    return retriever_tool


def create_iep_retriever_tool(user_id: str, k: int):
    # Create a retriever tool from embeddings in the specified user directory.
    base_directory = os.path.join('stored_embeds', user_id)

    embeddings = load_embeddings(base_directory)
    retriever = embeddings.as_retriever(search_type='similarity', search_kwargs={'k': k})
    print("Inside Create IEP")
    iep_retriever_tool = create_retriever_tool(
        retriever,
        f"IEP_Document_Retriever_{user_id}",
        "This retriever tool uses IEP embeddings from stored documents to find similar content based on semantic similarity. It is particularly effective for analyzing IEP documents and finding related information.",
    )

    return iep_retriever_tool


def load_embeddings(directory: str):
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory {directory} not found.")
    embeddings = OpenAIEmbeddings()
    return FAISS.load_local(directory, embeddings, allow_dangerous_deserialization=True)


def query_find_similar_embeddings(query: str, embeddings):
    results = embeddings.similarity_search(query)
    return results


