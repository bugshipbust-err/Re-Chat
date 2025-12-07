from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain.agents import create_agent
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from pydantic import BaseModel, Field
from typing import List, Dict, Literal

from prompt_gallery import query_gen_prompt, convo_summary_prompt, analyze_strings_prompt
from test_data import conversations
from rag_utils import make_single_query, format_conversation

# ------------------------------------------------------------------------------------------------------------------------------ #

class StringList(BaseModel):
    """ Used to suggest agent the 'QueryList' response format """
    queries: List[str] = Field(description="A list of strings")

class Choices(BaseModel):
    """ Used to suggest agent the 'Choices' response format """
    replacement: bool = Field(description="A boolean value, either 'True' or 'False'")
    # belongs: bool = Field(description="A boolean value, either 'True' or 'False'")

# ------------------------------------------------------------------------------------------------------------------------------ #

class UserRAG:
    def __init__(
            self,
            model_name: str,
            embedding_model_name: str,
            db_path: str,
            text_splitter: str,
        ):
        self.stringlist_agent = create_agent(
                ChatOllama(model=model_name),
                response_format=StringList,
            )
        self.decision_agent = create_agent(
                ChatOllama(model=model_name, format="json"),
                response_format=Choices,
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
    
    def extract_user_summary(
            self,
            conversation: List,
        ):
        convo_str = format_conversation(conversation)
        user_data_list = self.stringlist_agent.invoke({
                "messages": make_single_query(sys_prompt=convo_summary_prompt, usr_query=convo_str)
            })["structured_response"].queries

        return user_data_list

 
    def retrieve_data(
            self,
            query,
            k,
        ):
        sub_queries = self.stringlist_agent.invoke({
                "messages": make_single_query(sys_prompt=query_gen_prompt, usr_query=query)
            })["structured_response"].queries

        retrieved_data = []
        for query in sub_queries:
            retrieved_docs = self.vector_store.similarity_search(query, k=k)
            stitched_text_data = "\n".join([doc.page_content for doc in retrieved_docs])
            retrieved_data.append(stitched_text_data)

        return retrieved_data


    def injest_data(
            self,
            conversation: List,
            ret: Literal["items","ids"]=None,
        ):
        user_data_list = self.extract_user_summary(conversation)

        new_user_info = []
        for item in user_data_list:
            try:
                closest_item = self.vector_store.similarity_search(item, k=1)[0].page_content
            except Exception:
                closest_item = ""

            messages = make_single_query(sys_prompt=analyze_strings_prompt, usr_query=f"Str-1: {closest_item}\nStr-2: {item}")
            is_replacement = self.decision_agent.invoke({"messages": messages})["structured_response"].replacement

            if not is_replacement:
                print(f"Injesting: {item}")
                new_user_info.append(item)
            else:
                print(f"Skipping: {item}")

        ids = self.vector_store.add_texts(texts=new_user_info)
        if ret == "items":
            return new_user_info 
        if ret == "ids":
            return ids

# ------------------------------------------------------------------------------------------------------------------------------ #

def test(user_query, str1, str2):
    """
    Script to run tests on the UserRAG class
    """
    rag_agent = UserRAG(
            model_name="llama3.1",
            embedding_model_name="embeddinggemma:300m",
            db_path="./private/chroma_langchain_db",
            text_splitter="somesplitter",
        )
    
    # print(rag_agent.extract_user_summary(conversations[1]))
    # retrieved_data = rag_agent.retrieve_data(query=user_query, k=1)
    # for data in retrieved_data:
    #     print(data)

    # print(rag_agent.injest_data(conversations[1], ret="items"))
    # print(rag_agent.get_relation(prompt=analyze_strings_prompt, str1=str1, str2=str2))

    
# move this to test_data.py
str1 = "user was invited to a podcast where he spoke about his research work and his journey"
str2 = "he was also invited to some other podcasts in the past"
test_query = "how many years would a random guy with a undergrad degree need to reach a career position where im right now"
test_query = "RTX 3090"
test(user_query=test_query, str1=str1, str2=str2)
