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