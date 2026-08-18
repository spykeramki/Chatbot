from typing import Dict, List
from langgraph.graph import StateGraph, START, END

from openai import OpenAI

class State(Dict):
    messages: List[Dict[str, str]]

graph_builder = StateGraph(State)

bonsai_client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)


def chatbot(state: State):
    response = bonsai_client.chat.completions.create(
        model="prism-ml/bonsai-27b",
        messages=state["messages"],
        stream=True,
    )

    assistant_response = ""
    for chunk in response:
        if not chunk.choices:
            continue
        delta = getattr(chunk.choices[0], "delta", None)
        if delta and delta.content:
            token = delta.content
            assistant_response += token
    state["messages"].append({"role": "assistant", "content": assistant_response})
    return {"messages": state["messages"]}

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

graph = graph_builder.compile()

def stream_graph_updates(user_input: str):
    state = {"messages":[{"role": "user", "content": user_input}]}

    for event in graph.stream(state):
        for value in event.values():
            assistant_response = value["messages"][-1]["content"]
            print(f"Assistant: {assistant_response}\n")


    # Initialize chat history
# messages = [
#         {"role": "system", "content": "You are a helpful, direct local AI assistant."}
#     ]

# def chat_with_bonsai():
#     print("🤖 Local AI Session Started. Type 'quit' to exit.\n")
    

#     while True:
#         user_input = input("You: ")
#         if user_input.lower() == 'quit':
#             break
            
#         # Append user message to history
#         messages.append({"role": "user", "content": user_input})

#         try:
#             # 2. Call the local model
#             # Note: LM Studio automatically routes requests to whichever model is currently loaded,
#             # so the 'model' parameter string can be anything (e.g., "local-model").
#             response = bonsai_client.chat.completions.create(
#                 model="prism-ml/bonsai-27b",
#                 messages=messages,
#                 stream=True  # Enables word-by-word streaming responses
#             )

#             print("AI: ", end="", flush=True)
#             assistant_response = ""
            
#             # 3. Stream the tokens as they are generated
#             for chunk in response:
#                 if chunk.choices[0].delta.content:
#                     token = chunk.choices[0].delta.content
#                     print(token, end="", flush=True)
#                     assistant_response += token
#             print("\n")

#             # Append the assistant's reply to keep the conversation history
#             messages.append({"role": "assistant", "content": assistant_response})

#         except Exception as e:
#             print(f"\n❌ Error connecting to LM Studio: {e}")
#             print("Make sure the server is running in LM Studio and the port is correct.\n")

if __name__ == "__main__":
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['quit', 'exit']:
                print("Exiting the chat.")
                exit()

            stream_graph_updates(user_input)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Make sure the server is running in LM Studio and the port is correct.\n")