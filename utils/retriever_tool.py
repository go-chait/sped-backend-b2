import os
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.retrievers import EnsembleRetriever
from dotenv import load_dotenv
import logging

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("Did not find openai_api_key, please add an environment variable `OPENAI_API_KEY` which contains it, or pass `openai_api_key` as a named parameter.")

def create_ensemble_retriever(user_id: str, k: int):
    try:
        base_directory_iep = os.path.join('stored_embeds', user_id)
        base_directory_sped = os.path.join('stored_embeds')

        iep_embeddings = load_embeddings(base_directory_iep)
        sped_embeddings = load_embeddings(base_directory_sped)

        iep_retriever = iep_embeddings.as_retriever(search_type='similarity', search_kwargs={'k': k})
        sped_retriever = sped_embeddings.as_retriever(search_type='similarity', search_kwargs={'k': k})

        ensemble_retriever = EnsembleRetriever(
            retrievers=[iep_retriever, sped_retriever],
            weights=[0.5, 0.5]
        )

        return ensemble_retriever
    except Exception as e:
        logging.error(f"Error creating ensemble retriever: {e}")
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
