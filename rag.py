from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain.agents import create_agent
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from pydantic import BaseModel, Field
from typing import List

from prompt_gallery import query_gen_prompt

# ------------------------------------------------------------------------------------------------------------------------------ #

class QueryList(BaseModel):
    """ Used to suggest agent the 'QueryList' response format """
    queries: List[str] = Field(
        description="A list of text queries for vector search"
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
        """ 
        Initializing:
            query_agent     : returns a list of sub queries for an input query
            vector_store    : persistant vector database containing user information
        """
        self.query_agent = create_agent(
                ChatOllama(model=query_model_name),
                response_format=QueryList,
            )

        embedding_model = OllamaEmbeddings(model=embedding_model_name)
        self.vector_store = Chroma(
                collection_name="chroma_db",
                embedding_function=embedding_model,
                persist_directory=db_path,
            )
        self.text_sep_splitter = RecursiveCharacterTextSplitter(
                separators=".",
                keep_separator=False,
                chunk_size=1,               # force splitting at separator
                chunk_overlap=0,
            )

    def generate_queries(
            self,
            query: str,
        ) -> List[str]:
        """
        This method requests our query_agent to generate sub-queries for the user query
        Working:
            - passes in query_gen_prompt along with the query to the agent
                - query_gen_prompt  : instructions to return a list of sub queries
                - query             : query from main agent's tool call
        """
        messages = [
                {"role": "system", "content": query_gen_prompt},
                {"role": "user", "content": query}
            ]
        model_response = self.query_agent.invoke({
                "messages": messages
            })

        return model_response

    def retrieve_data(
            self,
            sub_queries,
            k,
        ):
        """
        Retrieve query data from the vector_store
        Algorithm:
            - run through every sub query, and get 'k' closest results for each of them
            - stitch them 'k' results together
            - append them to 'retrieved_data'
            - return 'retrieved_data'
        """
        retrieved_data = []
        for query in sub_queries:
            retrieved_docs = self.vector_store.similarity_search(query, k=k)
            stitched_text_data = "\n".join([doc.page_content for doc in retrieved_docs])
            retrieved_data.append(stitched_text_data)

        return retrieved_data


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

    agent_out = rag_agent.generate_queries(user_query)
    queries = agent_out["structured_response"].queries
    retrieved_data = rag_agent.retrieve_data(queries=queries, k=1)

    for data in retrieved_data:
        print(len(data))


# test_query = "how many years would a random guy with a undergrad degree need to reach a career position where im right now"
# test(user_query=test_query)
