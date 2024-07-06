from fastapi import FastAPI, HTTPException, Depends, APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_openai_tools_agent, AgentExecutor
# from langchain.tools import WebBrowserTool
import os
from utils.retriever_tool import create_retriever_tool_from_directory

router = APIRouter()

# Loading the key from .env file
load_dotenv()
open_ai_key = os.getenv('OPEN_AI_KEY')

# LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Create the retriever tool from the directory
k = 3  # Set the value of k as needed
retriever_tool = create_retriever_tool_from_directory(k)
tools = [retriever_tool]

# Prompt
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant to summarize the contents of a website"),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad")
    ]
)

# Defining Model and the Agent
agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

class URLRequest(BaseModel):
    url: str

@router.post('/summarize-website')
async def summarize_website(request: URLRequest):
    url = request.url
    
    try:
        query = f"Please summarize the content of the following website: {url}"

        # Perform the summarization using the retriever tool
        response =  agent_executor.invoke({"input": query})

        # Return the summary
        return {"summary": response["output"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error summarizing website: {str(e)}")
