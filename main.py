from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.tools import tool

# ------------------------------------------------------------------------------------------------------------------------------- #

llama = ChatOllama(model="llama3.1")
gemma = ChatOllama(model="gemma3:12b")
model = ChatOllama(model="gpt-oss:20b")

system_prompt = """
You are a helpful assistant who responds with personalized answers to the user's queries.
Keep your reponses really concise, short and straight to the point.
"""
retriever_desc = """
This is a user data retrieval tool that searches data relavant to you queries. Use this to answer queries that need additional information about the user
"""

# ------------------------------------------------------------------------------------------------------------------------------- #


@tool("user_data_retriever", description=retriever_desc)
def get_user_data(queries):
    return ["User works on LLM interpretablity", "He likes to code", "Uses neo-vim", "Works on a 3090 machine running linux mint"] 


agent = create_agent(
        model,
        tools=[get_user_data],
        system_prompt=system_prompt,
    )

messages = []

# ------------------------------------------------------------------------------------------------------------------------------- #

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
                print(f"content: {model_response}")
                messages.append({"role": "assistant", "content": model_response}) 
            else:
                print(f"step: {step}")
                print(f"content: {data['messages'][-1].content_blocks}")

# ------------------------------------------------------------------------------------------------------------------------------- #

print(len(messages))
