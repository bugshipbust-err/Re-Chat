from typing import List, Dict

# ------------------------------------------------------------------------------------------------------------------------------ #

def make_single_query(sys_prompt: str, usr_query: str) -> List[Dict]:
        return [{"role": "system", "content": sys_prompt}, {"role": "user", "content": usr_query}]

def format_conversation(conversation: List):
    formatted_conversation = ""

    for message in conversation:
        role = message['role'].upper()
        content = message['content']
        formatted_conversation += f"{role}: {content}\n\n"
        
    return formatted_conversation.strip() 

