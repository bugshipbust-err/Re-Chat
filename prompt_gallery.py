
# ---------------------------------------------------------- IN - USE ---------------------------------------------------------- #

system_prompt = """
You are a helpful assistant who responds with personalized responses to Neel's queries, who is the user.
Keep your reponses really concise, short and straight to the point.

When using the `user_data_retriever` tool:
    - call the tool WHENEVER you feel like having additional data about the user would help.
    - your query to the tool SHOULD contain essential keywords that will improve your search area.
    - ALWAYS provide a single string, and it DOES NOT have to be a single sentence.
    Example:
        [context: user wants to know what future career paths he/she would fit him]
        your_query: "What is user's current job role? What's his educational background? Things that facinate the user." 
"""

query_gen_prompt = (
        "Given a user query, break it into smaller semantic search queries "
        "Return ONLY a *list* of small queries or query "
        "DO NOT miss any possible sub query that can be drawn from the input query "
        "NEVER return a single string\n\n"
        "Example for multiple queries:\n" 
        "\tuser query: short summary of user's educational background\n"
        "\t\tyour output: ['schooling', 'university', 'mentors', 'undergrad subjects']\n"
        "Example for single query:\n"
        "\tuser query: when was i born?\n"
        "\t\tyour output: ['date of birth']\n"
    )

convo_summary_prompt = (
    "Given the conversation below between a USER and an ASSISTANT. Your job is to return a list of facts about the USER "
    "that you have learned from the conversation provided as a query. These facts should be concise, simple, and directly "
    "based on the user's statements during the conversation. The facts should reflect important details such as the "
    "user's interests, experiences, recent activities, and preferences. "
    "Your output should be a **list of simple factual statements** that summarize key points about the user. \n\n"

    "**EXAMPLE: **\n"
    "\t*query: *\n"
    "\t\tUSER: Hey, how are you doing?\n"
    "\t\tASSISTANT: Hey! I'm good, thanks. How can I help you today?\n"
    "\t\tUSER: I recently got invited to a podcast about my career and research journey. Can you help me summarize that?\n"
    "\t\tASSISTANT: Sure! Here's a quick summary of your career and research journey...\n"
    "\t\tUSER: Thanks, I also started working with IoT stuff. I'm using ESP32 modules and writing shell scripts.\n"
    "\t\tASSISTANT: That's awesome! Sounds like you're really into IoT projects now!\n"
    "\t\tUSER: I just recieved my new keyboard and i love it! it's really thockey.\n"
    "\t\tASSISTANT: Nice! A good keyboard can definitely boost your productivity!\n"
    "\t\tUSER: Yeah, but its not exactly a perfomance booster but definitely makes me want to type more. Hahaa!\n\n"
    
    "\t*Your response: *\n"
    "\t\t['User was invited to a podcast about their career and research journey', "
    "'User recently started working with IoT, using ESP32 modules and writing shell scripts',"
    "'User loves their new thockey keyboard and enjoys typing on it.']\n\n"

    "The facts should be objective and specific to the user.\n\n"
    "Be sure to extract *ONLY factual information about the user*, *NOT general comments* made by the user like: "
    "1. im doing good\t2. he wanted a summary of on his career\t3. his new keyboard didnt boost his productivity but made "
    "him type more. \n"
) 

analyze_strings_prompt = (
    "Given the two strings below, your job is to analyze and return a single boolean value: "
    "The boolean should indicate whether the information in Str-1 a replacement to Str-2 or not.\n Which in simpler terms "
    "can be framed as, Is *all* the information in Str-2 either *explicitly present* or *implied* in Str-1. "
    "If yes, then replacement: False, else replacement: True\n\n"
    
    "**EXAMPLE:**\n"
    "\t*Query:*\n"
    "\t\tStr-1: 'He recently adopted a Golden Retriever and takes it for a walk every evening.'\n"
    "\t\tStr-2: 'The user has a dog.'\n"
    "\t*Your response:*\n"
    "\t\treplacement: True\n"
    "\nExplanation: The second string 'The user has a dog' is implied in the first string because the user mentions adopting "
    "a Golden Retriever, which obviously is a dog. Therefore, the information is contained, and the response is `True`.\n\n"

    "**EXAMPLE:**\n"
    "\t*Query:*\n"
    "\t\tStr-1: 'User got a new car.'\n"
    "\t\tStr-2: 'He loves playing the guitar sitting alone in the car he bought.'\n"
    "\t*Your response:*\n"
    "\t\treplacement: False\n"
    "\nExplanation: str-1 does contain information about user's new car, but is missing information about how he loves to "
    "the guitar.\n\n" 
)

retriever_desc = "Gives you user-details. They *might* contain information you need to answer the query"

# ------------------------------------------------------ NOT - IN - USE -------------------------------------------------------- #
 
# retriever_desc = (
#         "Given a user question, break it into *at least 2–4* smaller semantic search queries."
#         "Return ONLY a list of short queries. "
#         "NEVER return a single string."
#     )
# 
# tool_message_content=(
#         "Return ONLY valid JSON matching the schema.\n"
#         "You MUST generate multiple short search queries.\n"
#         "Example:\n"
#         "{\n"
#         "  \"queries\": [\n"
#         "      \"user birthday\",\n"
#         "      \"Neel personal profile\",\n"
#         "      \"stored user facts\"\n"
#         "  ]\n"
#         "}\n"
#         "If it is a single query, return a list of that single string,\n"
#         "Example:\n"
#             "{\n"
#             "  \"queries\": [\n"
#             "      \"user birthday\",\n"
#             "  ]\n"
#             "}"
#     )

# ---------------------------------------------------------- YUM - G ----------------------------------------------------------- #

