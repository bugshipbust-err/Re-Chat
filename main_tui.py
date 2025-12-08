from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Horizontal, Vertical
from textual.widgets import Header, Footer, Input, Static, Button, Label, ListView, ListItem
from textual.screen import Screen, ModalScreen
from textual import work, on
from textual.message import Message

import os
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain.tools import tool
from typing import List

# Import your custom modules
# Assuming rag.py and prompt_gallery.py are in the same folder
from rag import UserRAG
from prompt_gallery import system_prompt, retriever_desc

# --- CSS Styles for the TUI ---
CSS = """
Screen {
    align: center middle;
}

/* Database Selection Screen */
#db-container {
    width: 60%;
    height: 70%;
    border: solid green;
    padding: 1 2;
    background: $surface;
}

/* Chat Screen */
#chat-container {
    height: 1fr;
    margin-bottom: 1;
    border: solid $accent;
    scrollbar-size: 1 1;
}

#input-container {
    height: auto;
    dock: bottom;
    padding: 0 1 1 1;
}

/* Message Bubbles */
.message {
    padding: 1 2;
    margin: 1 1;
    width: auto;
    max-width: 80%;
    height: auto;
    border: wide $background;
}

.user-message {
    dock: right;
    background: $primary-darken-2;
    color: white;
    text-align: right;
}

.assistant-message {
    dock: left;
    background: $surface-lighten-1;
    color: $text;
}

/* Ingest Modal */
#ingest-dialog {
    grid-size: 2;
    grid-gutter: 1 2;
    grid-rows: 1fr 3;
    padding: 0 1;
    width: 60;
    height: 11;
    border: thick $background 80%;
    background: $surface;
}

#ingest-label {
    column-span: 2;
    height: 1fr;
    content-align: center middle;
}

#ingest-buttons {
    column-span: 2;
    align: center middle;
}

Button {
    margin: 0 1;
}
"""

# --- Global / Shared State Wrapper ---
class GlobalState:
    rag_system = None
    chat_agent = None
    messages = []  # Stores the conversation history for ingestion

# --- Custom Widgets ---

class ChatBubble(Static):
    """A widget to display a single chat message."""
    pass

class DBSelectionScreen(Screen):
    """Screen to select the database at startup."""
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="db-container"):
            yield Label("Select a Database:", classes="header")
            
            # Scan directory
            db_dir_path = "./private/"
            items = []
            if os.path.exists(db_dir_path):
                dirs = [d for d in os.listdir(db_dir_path) if os.path.isdir(os.path.join(db_dir_path, d))]
                for d in dirs:
                    items.append(ListItem(Label(d), name=d))
            
            if not items:
                yield Label("No databases found in ./private/", style="red")
            else:
                yield ListView(*items, id="db-list")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected):
        chosen_db = event.item.name
        self.initialize_rag(chosen_db)
        
    def initialize_rag(self, chosen_db):
        query_model = "llama3.1"
        embedding_model = "embeddinggemma:300m"
        vector_db_path = f"./private/{chosen_db}"
        text_splitter = "nothing yet"

        # Initialize the UserRAG system
        rag_instance = UserRAG(
            model_name=query_model,
            embedding_model_name=embedding_model,
            db_path=vector_db_path,
            text_splitter=text_splitter,
        )

        # Define the tool (re-wrapped to access the specific instance)
        @tool("user_data_retriever", description=retriever_desc)
        def get_user_data(user_query: str) -> List[str]:
            data_list = rag_instance.retrieve_data(query=user_query, k=1)
            return data_list

        # Create the agent
        agent = create_agent(
            model=ChatOllama(model="gpt-oss:20b"),
            system_prompt=system_prompt,
            tools=[get_user_data],
        )

        # Save to global state
        GlobalState.rag_system = rag_instance
        GlobalState.chat_agent = agent
        
        # Switch to the main chat screen
        self.app.push_screen(ChatScreen())

class IngestModal(ModalScreen):
    """Modal to ask for ingestion."""
    
    def compose(self) -> ComposeResult:
        with Vertical(id="ingest-dialog"):
            yield Label("Conversation ended.\nDo you want to ingest this conversation into the DB?", id="ingest-label")
            with Horizontal(id="ingest-buttons"):
                yield Button("Yes", variant="success", id="btn-yes")
                yield Button("No", variant="error", id="btn-no")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-yes":
            self.dismiss(True)
        else:
            self.dismiss(False)

class ChatScreen(Screen):
    """The main chat interface."""
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(id="chat-container")
        with Vertical(id="input-container"):
            yield Input(placeholder="Type your message... (type 'xx' to exit)")

    async def on_input_submitted(self, event: Input.Submitted):
        user_query = event.value
        event.input.value = ""  # Clear input

        if not user_query.strip():
            return

        # Handle Exit
        if user_query.strip() == "xx":
            self.trigger_exit_sequence()
            return

        # Add User Message to UI
        await self.add_message(user_query, is_user=True)
        
        # Add User Message to History
        GlobalState.messages.append({"role": "user", "content": user_query})

        # Create a placeholder for the assistant's response
        assistant_bubble = await self.add_message("Thinking...", is_user=False)
        
        # Run the agent in a background thread
        self.stream_agent_response(user_query, assistant_bubble)

    async def add_message(self, text, is_user):
        container = self.query_one("#chat-container")
        bubble = ChatBubble(text)
        bubble.add_class("message")
        bubble.add_class("user-message" if is_user else "assistant-message")
        await container.mount(bubble)
        container.scroll_end(animate=False)
        return bubble

    # --- FIX START ---
    # Removed 'async'. This forces Textual to run it in a separate thread.
    @work(exclusive=True, thread=True)
    def stream_agent_response(self, user_query, bubble_widget):
        """Runs the LangChain agent loop in a thread to avoid freezing UI."""
        
        full_response = ""
        first_token_received = False

        # Access the agent from global state
        chat_agent = GlobalState.chat_agent
        messages = GlobalState.messages 

        try:
            # This is a blocking generator, so it MUST run in a thread (not async)
            for chunk in chat_agent.stream({"messages": messages}, stream_mode="updates"):
                for step, data in chunk.items():
                    last_content_block = data['messages'][-1].content_blocks
                    
                    if step == "model" and last_content_block[-1]["type"] == "text":
                        model_chunk = last_content_block[-1]["text"]
                        
                        if not first_token_received:
                            # Safely update UI from thread
                            self.app.call_from_thread(bubble_widget.update, "")
                            first_token_received = True
                        
                        full_response = model_chunk 
                        self.app.call_from_thread(bubble_widget.update, full_response)
                        
                    else:
                        pass

            if full_response:
                GlobalState.messages.append({"role": "assistant", "content": full_response})
            else:
                if not first_token_received:
                     self.app.call_from_thread(bubble_widget.update, "No text response generated (Tool used).")

        except Exception as e:
            self.app.call_from_thread(bubble_widget.update, f"Error: {str(e)}")
    # --- FIX END ---

    def trigger_exit_sequence(self):
        def check_ingest(should_ingest: bool):
            if should_ingest:
                if GlobalState.rag_system:
                    try:
                        self.notify("Ingesting data...")
                        GlobalState.rag_system.injest_data(GlobalState.messages)
                    except Exception as e:
                        pass 
            self.app.exit()

        self.app.push_screen(IngestModal(), check_ingest)
# --- Main App ---

class RagTuiApp(App):
    CSS = CSS

    def on_mount(self):
        self.push_screen(DBSelectionScreen())

if __name__ == "__main__":
    app = RagTuiApp()
    app.run()
