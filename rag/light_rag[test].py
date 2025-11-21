import asyncio
import os
import inspect
import logging
import logging.config
from lightrag import LightRAG, QueryParam
from lightrag.llm.ollama import ollama_model_complete, ollama_embed
from lightrag.utils import EmbeddingFunc, logger, set_verbose_debug

from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=False)

WORKING_DIR = "./dickens"

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)


async def initialize_rag():
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=ollama_model_complete,
        llm_model_name=os.getenv("LLM_MODEL", "llama3.1:latest"),
        summary_max_tokens=8192,
        llm_model_kwargs={
            "host": os.getenv("LLM_BINDING_HOST", "http://localhost:11434"),
            "options": {"num_ctx": 8192},
            "timeout": int(os.getenv("TIMEOUT", "300")),
        },
        embedding_func=EmbeddingFunc(
            embedding_dim=int(os.getenv("EMBEDDING_DIM", "1024")),
            max_token_size=int(os.getenv("MAX_EMBED_TOKENS", "8192")),
            func=lambda texts: ollama_embed(
                texts,
                embed_model=os.getenv("EMBEDDING_MODEL", "nomic-embed-text"),
                host=os.getenv("EMBEDDING_BINDING_HOST", "http://localhost:11434"),
            ),
        ),
    )

    await rag.initialize_storages()  # Auto-initializes pipeline_status
    return rag


async def print_stream(stream):
    async for chunk in stream:
        print(chunk, end="", flush=True)


async def main():
    try:
        # Initialize RAG instance
        rag = await initialize_rag()

        # Test embedding function
        test_text = ["This is a test string for embedding."]
        embedding = await rag.embedding_func(test_text)
        embedding_dim = embedding.shape[1]
        print("\n=======================")
        print("Test embedding function")
        print("========================")
        print(f"Test dict: {test_text}")
        print(f"Detected embedding dimension: {embedding_dim}\n\n")

        with open("./book.txt", "r", encoding="utf-8") as f:
            await rag.ainsert(f.read())

        # Perform hybrid search
        print("\n=====================")
        print("Query mode: hybrid")
        print("=====================")
        resp = await rag.aquery(
            "What are the top themes in this story?",
            param=QueryParam(mode="hybrid", stream=True),
        )
        if inspect.isasyncgen(resp):
            await print_stream(resp)
        else:
            print(resp)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if rag:
            await rag.llm_response_cache.index_done_callback()
            await rag.finalize_storages()


if __name__ == "__main__":
    asyncio.run(main())
    print("\nDone!")
