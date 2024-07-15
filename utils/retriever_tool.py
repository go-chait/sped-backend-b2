import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.tools.retriever import create_retriever_tool
from dotenv import load_dotenv
import logging

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("Did not find openai_api_key, please add an environment variable `OPENAI_API_KEY` which contains it, or pass `openai_api_key` as a named parameter.")

def create_retriever_tool_from_directory(k: int):
    try:
        base_directory = os.path.join('stored_embeds')
        embeddings = load_embeddings(base_directory)
        retriever = embeddings.as_retriever(search_type='similarity', search_kwargs={'k': k})
        retriever_tool = create_retriever_tool(
            retriever,
            "SPED_Retriever_Tool",
            "This retriever tool uses embeddings from stored documents to find similar content based on semantic similarity. It is particularly effective for summarizing web pages and finding related information.",
        )
        return retriever_tool
    except Exception as e:
        logging.error(f"Error creating retriever tool from directory: {e}")
        raise

def create_iep_retriever_tool(user_id: str, k: int):
    try:
        base_directory = os.path.join('stored_embeds', user_id)
        embeddings = load_embeddings(base_directory)
        retriever = embeddings.as_retriever(search_type='similarity', search_kwargs={'k': k})
        iep_retriever_tool = create_retriever_tool(
            retriever,
            f"IEP_Retriever_Tool_{user_id}",
            "This retriever tool uses IEP embeddings from stored documents to find similar content based on semantic similarity. It is particularly effective for analyzing IEP documents and finding related information.",
        )
        return iep_retriever_tool
    except Exception as e:
        logging.error(f"Error creating IEP retriever tool for user {user_id}: {e}")
        raise

def load_embeddings(directory: str):
    try:
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Directory {directory} not found.")
        embeddings = OpenAIEmbeddings()
        return FAISS.load_local(directory, embeddings, allow_dangerous_deserialization=True)
    except Exception as e:
        logging.error(f"Error loading embeddings from directory {directory}: {e}")
        raise
