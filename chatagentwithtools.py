import json
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from typing import Dict, Annotated
from langgraph.graph.message import add_messages

from openai import OpenAI

from tools.searxng.searxng import web_search_tool
from IPython.display import Image, HTML, display


class State(Dict):
    messages: Annotated[list, add_messages]

bonsai_client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

def addition_tool(a: int, b: int):
    """Add two numbers."""
    return {"result": a + b}

openai_tools = [{
    "type": "function",
    "function": {
        "name": "web_search_tool",
        "description": "Search the web for current information.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query.",
                },
            },
            "required": ["query"],
        },
    },
}, {
    "type": "function",
    "function": {
        "name": "addition_tool",
        "description": "Add two numbers together.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "integer",
                    "description": "The first number.",
                },
                "b": {
                    "type": "integer",
                    "description": "The second number.",
                },
            },
            "required": ["a", "b"],
        },
    },
}]

tool_node = ToolNode([web_search_tool, addition_tool])


def openai_messages(messages):
    converted = []
    role_map = {
        "human": "user",
        "ai": "assistant",
        "system": "system",
        "tool": "tool",
    }
    for message in messages:
        if isinstance(message, dict):
            converted.append(message)
            continue

        openai_message = {
            "role": role_map[message.type],
            "content": message.content,
        }
        if message.type == "ai" and message.tool_calls:
            openai_message["tool_calls"] = [
                {
                    "id": tool_call["id"],
                    "type": "function",
                    "function": {
                        "name": tool_call["name"],
                        "arguments": json.dumps(tool_call["args"]),
                    },
                }
                for tool_call in message.tool_calls
            ]
        if message.type == "tool":
            openai_message["tool_call_id"] = message.tool_call_id
        converted.append(openai_message)
    return converted


def chatbot(state: State):
    messages = state["messages"]
    response = bonsai_client.chat.completions.create(
        model="prism-ml/bonsai-27b",
        messages=openai_messages(messages),
        tools=openai_tools,
        tool_choice="auto",
    )

    assistant_message = response.choices[0].message
    return {"messages": [assistant_message.model_dump(exclude_none=True)]}


graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
graph = graph_builder.compile()

display(Image(graph.get_graph().draw_mermaid_png()))


def stream_graph_updates(user_input: str):
    state = {"messages": [{"role": "user", "content": user_input}]}
    for event in graph.stream(state):
        for value in event.values():
            last_message = value["messages"][-1]
            message_type = getattr(last_message, "type", None)
            message_role = last_message.get("role") if isinstance(last_message, dict) else None
            tool_calls = getattr(last_message, "tool_calls", None)
            if isinstance(last_message, dict):
                tool_calls = last_message.get("tool_calls")
            if tool_calls:
                continue
            if message_type not in (None, "ai") and message_role != "assistant":
                continue
            content = getattr(last_message, "content", None)
            if isinstance(last_message, dict):
                content = last_message.get("content")
            if content:
                print(f"Assistant: {content}\n")


if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "done"]:
            break
        stream_graph_updates(user_input)