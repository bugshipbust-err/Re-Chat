import os
import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static, TextLog, Button

# --- Existing imports from your script ---
from langchain_ollama import ChatOllama
from langchain.tools import tool
from langchain.agents import create_agent
from typing import List

from rag import UserRAG
from prompt_gallery import system_prompt, retriever_desc

# -------------------------------------------------------------------------------------------------- #

class ChatScreen(App):
    CSS_PATH = None

    def __init__(self):
        super().__init__()
        self.messages = []
        self.rag_system = None
        self.chat_agent = None
        self.current_db = None

    # ---------------------------- UI Layout ---------------------------------- #
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield TextLog(id="log", highlight=True, wrap=True)
        yield Input(placeholder="You: ", id="input")
        yield Footer()

    async def on_mount(self):
        await self.choose_db()
        await self.setup_agent()

    # ---------------------------- Choose DB ---------------------------------- #
    async def choose_db(self):
        log = self.query_one("#log", TextLog)
        db_dir_path = "./private/"

        db_names = [d for d in os.listdir(db_dir_path) if os.path.isdir(os.path.join(db_dir_path, d))]

        log.write("Select a Database:\n")
        for i, name in enumerate(db_names):
            log.write(f"{i}. {name}")

        async with self.input_prompt("Enter DB number: ") as value:
            idx = int(value)
            self.current_db = db_names[idx]
            log.write(f"Using DB: {self.current_db}\n")

    # ---------------------------- Setup Agent ---------------------------------- #
    async def setup_agent(self):
        query_model = "llama3.1"
        embedding_model = "embeddinggemma:300m"

        vector_db_path = f"./private/{self.current_db}"

        self.rag_system = UserRAG(
            model_name=query_model,
            embedding_model_name=embedding_model,
            db_path=vector_db_path,
            text_splitter="nothing yet",
        )

        @tool("user_data_retriever", description=retriever_desc)
        def get_user_data(user_query: str) -> List[str]:
            data_list = self.rag_system.retrieve_data(query=user_query, k=1)
            return data_list

        self.chat_agent = create_agent(
            model=ChatOllama(model="gpt-oss:20b"),
            system_prompt=system_prompt,
            tools=[get_user_data],
        )

    # ---------------------------- Main Chat Loop ---------------------------------- #
    async def on_input_submitted(self, event: Input.Submitted):
        user_query = event.value
        input_box = self.query_one("#input", Input)
        log = self.query_one("#log", TextLog)

        input_box.value = ""  # clear input

        if user_query.strip() == "xx":
            await self.ask_to_save()
            return

        # Log user message
        log.write(f"You: {user_query}\n")
        self.messages.append({"role": "user", "content": user_query})

        # Handle model streaming
        async for chunk in self.chat_agent.astream({"messages": self.messages}, stream_mode="updates"):
            for step, data in chunk.items():
                last_content_block = data['messages'][-1].content_blocks

                # Only model text output
                if step == "model" and last_content_block[-1]["type"] == "text":
                    model_resp = last_content_block[-1]["text"]
                    log.write(f"Model: {model_resp}\n")
                    self.messages.append({"role": "assistant", "content": model_resp})
                else:
                    # Skip tool call logs completely
                    pass

    # ---------------------------- Save DB? ---------------------------------- #
    async def ask_to_save(self):
        log = self.query_one("#log", TextLog)
        async with self.input_prompt("Save conversation to DB? (y/n): ") as value:
            if value.lower().strip() == "y":
                self.rag_system.injest_data(self.messages)
                log.write("Conversation saved!\n")
            else:
                log.write("Not saved.\n")
        await asyncio.sleep(1)
        await self.action_quit()

    # ---------------------------- Input Prompt Helper ---------------------------------- #
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def input_prompt(self, prompt_text: str):
        log = self.query_one("#log", TextLog)
        input_box = self.query_one("#input", Input)

        log.write(prompt_text)
        input_box.placeholder = prompt_text
        input_box.value = ""

        # Wait for next input
        result = await self.wait_for(Input.Submitted)
        yield result.value

        input_box.placeholder = "You: "


# ------------------------------------------------------------------------------------------- #
if __name__ == "__main__":
    app = ChatScreen()
    app.run()

