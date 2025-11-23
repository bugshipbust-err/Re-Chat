from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
# ------------------------------------------------------------------------------------------------------------------------------ #

def load_txt(f_name):
    with open(f_name) as f:
        text = f.read()
    return text 

# ------------------------------------------------------------------------------------------------------------------------------ #

embeddings = OllamaEmbeddings(model="embeddinggemma:300m")

vector_store = Chroma(
        collection_name="chroma_db",
        embedding_function=embeddings,
        persist_directory="./private/chroma_langchain_db",
    )

text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=250,
        chunk_overlap=50,
        add_start_index=True,
    )
text_sep_splitter = RecursiveCharacterTextSplitter(
        separators="\n",
        keep_separator=False,
        chunk_size=1,               # force splitting at separator
        chunk_overlap=0,
    )

# ------------------------------------------------------------------------------------------------------------------------------ #

# sample = load_txt(f_name="neel_text.txt")
# text_splits = text_sep_splitter.split_text(sample)
# 
# documents = [Document(page_content=text_split) for text_split in text_splits]
# document_ids = vector_store.add_documents(documents=documents)
 
query = "neel nanda"
retrieved_docs = vector_store.similarity_search(query, k=2)

print(retrieved_docs)

