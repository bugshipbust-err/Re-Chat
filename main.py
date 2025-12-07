from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain.agents import AgentState, create_agent
from langchain.tools import tool
from langchain.agents.structured_output import ToolStrategy
from langchain_chroma import Chroma
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.agents.middleware import ModelRequest, ModelResponse, wrap_model_call

from pydantic import BaseModel, Field
from typing import List

from rag import UserRAG
from prompt_gallery import system_prompt, retriever_desc

# ------------------------------------------------------------------------------------------------------------------------------- #

query_model = "llama3.1"
embedding_model = "embeddinggemma:300m"
vector_db_path = "./private/chroma_db[main]"
text_splitter = "nothing yet"

# ------------------------------------------------------------------------------------------------------------------------------- #

rag_system = UserRAG(
        model_name=query_model,
        embedding_model_name=embedding_model,
        db_path=vector_db_path,
        text_splitter=text_splitter,
    )

@tool("user_data_retriever", description=retriever_desc)
def get_user_data(user_query: str) -> List[str]:
    data_list = rag_system.retrieve_data(query=user_query, k=1)
    return data_list


chat_agent = create_agent(
        model=ChatOllama(model="gpt-oss:20b"),
        system_prompt=system_prompt,
        tools=[get_user_data],
)

# ------------------------------------------------------------------------------------------------------------------------------- #

messages = []

while True:
    user_query = input("You: ")
    if user_query == "xx":
        break 
    messages.append({"role": "user", "content": user_query})
    
    for chunk in chat_agent.stream({"messages": messages}, stream_mode="updates"):
        for step, data in chunk.items():
            last_content_block = data['messages'][-1].content_blocks
            
            # Checking if the message is to the user or not
            if step == "model" and last_content_block[-1]["type"] == "text":    # last_content_block is a list - batch ig - so 1 
                model_response = last_content_block[-1]["text"]
                print(f"Model Response: {model_response}\n")
                messages.append({"role": "assistant", "content": model_response}) 
            else:
                print(f"step: {step}")
                print(f"content: {data['messages'][-1].content_blocks}\n")

if input("Do we injest the convo(y/n): ") == "y":
    rag_system.injest_data(messages)

# ------------------------------------------------------------------------------------------------------------------------------- #

