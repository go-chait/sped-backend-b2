from fastapi import HTTPException, APIRouter, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
import os
from core.security.security import require_auth
from utils.retriever_tool import create_retriever_tool_from_directory
from pymongo import MongoClient
from datetime import datetime
from db.mongodb import Conversations
router = APIRouter()

# Load environment variables
load_dotenv()
open_ai_key = os.getenv('OPEN_AI_KEY')

# LLM setup
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
memory = ConversationBufferMemory(memory_key="chat_history")

k = 3
retriever_tool = create_retriever_tool_from_directory(k)
tools = [retriever_tool]

# Prompt setup
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant to summarize the contents of a website"),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad")
    ]
)

agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

class URLRequest(BaseModel):
    query: str

@router.post('/agent-testing')
async def agent_testing(request: URLRequest, auth: dict = Depends(require_auth)):
    user_id =  auth['userId']
    query = request.query
    try:
        # Perform the summarization using the retriever tool
        response = agent_executor.invoke({"input": query})
        summary = response["output"]
        
        # Create conversation entry
        conversation_entry = {
            "question": query,
            "AI": summary,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Find the user conversation document or create a new one if it doesn't exist
        user_conversation = Conversations.find_one({"user_id": user_id})
        if user_conversation:
            # Update the existing document by appending the new conversation entry
            Conversations.update_one(
                {"user_id": user_id},
                {"$push": {"conversation": conversation_entry}}
            )
        else:
            # Create a new document for the user
            new_user_conversation = {
                "user_id": user_id,
                "conversation": [conversation_entry]
            }
            Conversations.insert_one(new_user_conversation)
        
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error Agent: {str(e)}")






# from fastapi import HTTPException, APIRouter
# from pydantic import BaseModel
# from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain.agents import create_openai_tools_agent, AgentExecutor
# # from langchain.tools import WebBrowserTool
# import os
# from utils.retriever_tool import create_retriever_tool_from_directory
# from langchain.memory import ConversationBufferMemory

# router = APIRouter()

# load_dotenv()
# open_ai_key = os.getenv('OPEN_AI_KEY')

# llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
# memory = ConversationBufferMemory(memory_key="chat_history")

# k = 3  
# retriever_tool = create_retriever_tool_from_directory(k)
# tools = [retriever_tool]

# # Prompt
# prompt = ChatPromptTemplate.from_messages(
#     [
#         ("system", "You are a helpful assistant to summarize the contents of a website"),
#         MessagesPlaceholder("chat_history", optional=True),
#         ("human", "{input}"),
#         MessagesPlaceholder("agent_scratchpad")
#     ]
# )

# agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)
# agent_executor = AgentExecutor(agent=agent, tools=tools)

# class URLRequest(BaseModel):
#     query: str

# @router.post('/agent-testing')
# async def agent_testing(request: URLRequest):
    
#     query = request.query
#     try:
#         # retrieved_content = agent_executor.invoke({"input": query})["output"]
#         # print(f"Retrieved content length: {len(retrieved_content)} tokens")

#         response =  agent_executor.invoke({"input": query})

#         return {"summary": response["output"]}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error Agent: {str(e)}")
