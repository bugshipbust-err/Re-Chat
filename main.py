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
vector_db_path = "./private/chroma_langchain_db"
text_splitter = "nothing yet"

# ------------------------------------------------------------------------------------------------------------------------------- #

rag_system = UserRAG(
        query_model_name=query_model,
        embedding_model_name=embedding_model,
        db_path=vector_db_path,
        text_splitter=text_splitter,
    )

@tool("user_data_retriever", description=retriever_desc)
def get_user_data(
        user_query: str
    ) -> List[str]:
    sub_queries = rag_system.generate_queries(user_query)
    data_list = rag_system.retrieve_data(sub_queries=sub_queries, k=1)
    return data_list


agent = create_agent(
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
    
    for chunk in agent.stream({"messages": messages}, stream_mode="updates"):
        for step, data in chunk.items():
            last_content_block = data['messages'][-1].content_blocks

            if step == "model" and last_content_block[-1]["type"] == "text":    # last_content_block is a list - batch ig - so 1 
                model_response = last_content_block[-1]["text"]
                print(f"\nModel Response:\n{model_response}")
                messages.append({"role": "assistant", "content": model_response}) 
            else:
                print(f"\nstep: {step}")
                print(f"content: {data['messages'][-1].content_blocks}")

# ------------------------------------------------------------------------------------------------------------------------------- #

