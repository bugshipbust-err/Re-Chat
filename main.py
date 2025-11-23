from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.agents.structured_output import ToolStrategy
from langchain_chroma import Chroma
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse

from pydantic import BaseModel, Field
from typing import List

from prompt_gallery import system_prompt, retriever_desc, tool_message_content

# ------------------------------------------------------------------------------------------------------------------------------- #

llama = ChatOllama(model="llama3.1")
gemma = ChatOllama(model="gemma3:12b")
model = ChatOllama(model="gpt-oss:20b")

embeddings = OllamaEmbeddings(model="embeddinggemma:300m")
vector_store = Chroma(
        collection_name="chroma_db",
        embedding_function=embeddings,
        persist_directory="./private/chroma_langchain_db",
    )
text_sep_splitter = RecursiveCharacterTextSplitter(
        separators=".",
        keep_separator=True,
        chunk_size=1,               # force splitting at separator
        chunk_overlap=0,
    )

class QueryList(BaseModel):
    queries: List[str] = Field(
        description="A list of text queries for vector search"
    )

# ------------------------------------------------------------------------------------------------------------------------------- #

@tool("user_data_retriever", description=retriever_desc)
def get_user_data(queries):
    ret_str = ""
    for query in queries:
        print(query)
        retrieved_docs = vector_store.similarity_search(query, k=2)
        stitched_text_data = [doc.page_content for doc in retrieved_docs]
        ret_str += "\n".join(stitched_text_data)
    return ret_str

agent = create_agent(
        model,
        tools=[get_user_data],
        response_format=ToolStrategy(schema=QueryList, tool_message_content=tool_message_content),
        system_prompt=system_prompt,
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
                print(f"\n\nModel Response:\n{model_response}")
                messages.append({"role": "assistant", "content": model_response}) 
            else:
                print(f"\n\nstep: {step}")
                print(f"content: {data['messages'][-1].content_blocks}")

# ------------------------------------------------------------------------------------------------------------------------------- #

