from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
import os
import logging
from utils.retriever_tool import create_ensemble_retriever
from db.mongodb import Conversations
import datetime

router = APIRouter()

load_dotenv()
open_ai_key = os.getenv('OPENAI_API_KEY')


if not open_ai_key:
    raise ValueError("OPEN_AI_KEY environment variable not set")


llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=open_ai_key)


k = 3


store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Integrate with RunnableWithMessageHistory
class ChatRequest(BaseModel):
    user_id: str
    question: str

@router.post('/summarize-website')
async def summarize_website(request: ChatRequest):
    print("REQUEST", request)
    user_id = request.user_id
    question = request.question
    print("user id", user_id)

    try:
        # Create the ensemble retriever tool
        ensemble_retriever_tool = create_ensemble_retriever(user_id, k)
        print("Ensemble Retriever Tool Created")

        # Prompt
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a knowledgeable assistant specializing in education. Your task is to review the provided Individualized Education Program (IEP) document and evaluate it against the Special Education (SPED) strategic plan stored in the vector databases. Please identify key details and perform a comparative analysis."),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )

        # Define the select_chat_agent function
        def select_chat_agent(llm, retriever, prompt):
            runnable = prompt | llm
            return RunnableWithMessageHistory(
                runnable,
                get_session_history,
                input_messages_key="input",
                history_messages_key="history",
                retriever=retriever
            )

        # Create the agent
        agent = select_chat_agent(llm, ensemble_retriever_tool, prompt)

        query = f"{question}"

        # Perform the summarization using the agent
        response = agent.invoke(
            {"input": query},
            config={"configurable": {"session_id": user_id}}
        )

        # Handle the response object correctly
        ai_answer = response.content if hasattr(response, 'content') else response

        current_timestamp = datetime.datetime.utcnow()

        # Prepare the conversation data
        conversation_entry = {
            "question": question,
            "Ai_answer": ai_answer,
            "timestamp": current_timestamp,
        }

        session_data = Conversations.find_one({"userId": user_id})
        if session_data:
            # Update the existing user conversation
            Conversations.update_one(
                {"userId": user_id},
                {"$push": {"conversations": conversation_entry}}
            )
        else:
            # Create a new user conversation
            Conversations.insert_one({
                "userId": user_id,
                "conversations": [conversation_entry]
            })

        # Fetch updated conversation history
        updated_conversations = Conversations.find_one({"userId": user_id}, {"_id": 0, "conversations": 1})

        return {"summary": ai_answer, "conversations": updated_conversations['conversations']}
    except Exception as e:
        logging.error(f"Error during summarization: {e}")
        raise HTTPException(status_code=500, detail=f"Error summarizing website: {str(e)}")

@router.get('/conversations/{user_id}')
async def get_conversations(user_id: str):
    try:
        user_data = Conversations.find_one({"userId": user_id}, {"_id": 0, "conversations": 1})
        if not user_data:
            raise HTTPException(status_code=404, detail="User conversations not found")

        return {"conversations": user_data['conversations']}
    except Exception as e:
        logging.error(f"Error fetching conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching conversations: {str(e)}")
