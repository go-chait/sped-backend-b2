import os
import json
import re
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.tools.retriever import create_retriever_tool
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("Did not find openai_api_key, please add an environment variable `OPENAI_API_KEY` which contains it, or pass `openai_api_key` as a named parameter.")

def create_retriever_tool_from_directory(base_directory: str, k: int):
    # Create a retriever tool from embeddings in the specified directory.
    # example: base_directory = r'stored_embeds\\files'
    
    embedding_dirs = get_embedding_directories(base_directory)
    
    if not embedding_dirs:
        raise ValueError(f"No embeddings found in directory: {base_directory}")
    
    # Load the embeddings from the most recent directory (the directories are timestamped)
    most_recent_dir = sorted(embedding_dirs, key=lambda x: os.path.getmtime(x))[-1]
    
    
    embeddings = load_embeddings(most_recent_dir)
    retriever = embeddings.as_retriever(search_type='similarity', search_kwargs={'k': k})
    
    retriever_tool = create_retriever_tool(
        retriever,
        "retriever_name",
        "A detailed description of the retriever and when the agent should use it.",
    )
    
    return retriever_tool


def load_embeddings(directory: str):
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory {directory} not found.")
    embeddings = OpenAIEmbeddings()
    return FAISS.load_local(directory, embeddings, allow_dangerous_deserialization=True)


def query_find_similar_embeddings(query: str, embeddings):
    results = embeddings.similarity_search(query)
    return results


def get_embedding_directories(base_directory: str):
    
    # Get all embedding subdirectories within the base directory.
    # Example: base_directory = r'stored_embeds\\files'
    
    embedding_dirs = []
    for root, dirs, files in os.walk(base_directory):
        if 'index.faiss' in files:
            embedding_dirs.append(root)
    return embedding_dirs


# just in case:
def get_embeddings_for_query(query: str):
    # Load all embeddings from both URL and file sources and search for the query.
    base_directories = []

    url_mapping_file = os.path.join('stored_embeds', 'url_mapping.json')
    if os.path.exists(url_mapping_file):
        with open(url_mapping_file, 'r') as f:
            url_hash_to_dir = json.load(f)
            base_directories.extend(url_hash_to_dir.values())
    
    file_mapping_file = os.path.join('stored_embeds', 'file_mapping.json')
    if os.path.exists(file_mapping_file):
        with open(file_mapping_file, 'r') as f:
            file_hash_to_dir = json.load(f)
            base_directories.extend(file_hash_to_dir.values())

    all_results = []
    for base_dir in base_directories:
        embedding_dirs = get_embedding_directories(base_dir)
        for directory in embedding_dirs:
            try:
                embeddings = load_embeddings(directory)
                results = query_find_similar_embeddings(query, embeddings)
                all_results.extend(results)
            except FileNotFoundError:
                continue

    return all_results

