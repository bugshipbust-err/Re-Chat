from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain.agents import create_agent
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from pydantic import BaseModel, Field
from typing import List, Dict

from prompt_gallery import query_gen_prompt, convo_summary_prompt
from test_data import conversations

# ------------------------------------------------------------------------------------------------------------------------------ #

class StringList(BaseModel):
    """ Used to suggest agent the 'QueryList' response format """
    queries: List[str] = Field(
        description="A list of text queries for vector search"
    )

class Boolean(BaseModel):
    """ Used to suggest agent the 'QueryList' response format """
    queries: bool = Field(
        description="A boolean value, either 'True' or 'False'"
    )

# ------------------------------------------------------------------------------------------------------------------------------ #

class UserRAG:
    def __init__(
            self,
            query_model_name: str,
            embedding_model_name: str,
            db_path: str,
            text_splitter: str,
        ):
        self.db_manager = create_agent(
                ChatOllama(model=query_model_name),
                response_format=StringList,
            )
        self.db_manager = create_agent(
                ChatOllama(model=query_model_name),
                response_format=,
            )


        self.vector_store = Chroma(
                collection_name="chroma_db",
                embedding_function=OllamaEmbeddings(model=embedding_model_name),
                persist_directory=db_path,
            )
        self.text_sep_splitter = RecursiveCharacterTextSplitter(
                separators=".",
                keep_separator=False,
                chunk_size=1,               # force splitting at separator
                chunk_overlap=0,
            )


    def prompt_invoke(
            self,
            prompt: str,
            query: str,
        ) -> List[str]:
        messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": query}
            ]
        agent_response = self.db_manager.invoke({
                "messages": messages,
            })

        return agent_response


    def stitch_convo(
            self,
            conversation, 
        ):
        formatted_conversation = ""

        for message in conversation:
            role = message['role'].upper()
            content = message['content']
            formatted_conversation += f"{role}: {content}\n\n"
        
        return formatted_conversation.strip() 


    def retrieve_data(
            self,
            query,
            k,
        ):
        sub_queries = self.prompt_invoke(
                prompt=query_gen_prompt,
                query=query,
            )["structured_response"].queries

        retrieved_data = []
        for query in sub_queries:
            retrieved_docs = self.vector_store.similarity_search(query, k=k)
            stitched_text_data = "\n".join([doc.page_content for doc in retrieved_docs])
            retrieved_data.append(stitched_text_data)

        return retrieved_data


    def injest_data(
            self,
            conversation: str,
        ):
        convo_str = self.stitch_convo(conversation)
        user_data_list = self.prompt_invoke(
                prompt=convo_summary_prompt, 
                query=convo_str, 
            )["structured_response"].queries
       
        return user_data_list
         

# ------------------------------------------------------------------------------------------------------------------------------ #

def test(user_query):
    """
    Script to run tests on the UserRAG class
    """
    rag_agent = UserRAG(
            query_model_name="llama3.1",
            embedding_model_name="embeddinggemma:300m",
            db_path="./private/chroma_langchain_db",
            text_splitter="somesplitter",
        )

    retrieved_data = rag_agent.retrieve_data(query=user_query, k=2)
    for data in retrieved_data:
        print(len(data))

    print(rag_agent.injest_data(conversations[1]))
    
# move this to test_data.py
test_query = "how many years would a random guy with a undergrad degree need to reach a career position where im right now"
test(user_query=test_query)
