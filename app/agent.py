from functools import lru_cache
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from app.config import settings


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


@lru_cache(maxsize=1)
def get_agent():
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY must be configured before generating replies.")

    model = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.4,
    )
    graph = StateGraph(ChatState)
    graph.add_node("assistant", lambda state: {"messages": [model.invoke(state["messages"])]})
    graph.add_edge(START, "assistant")
    graph.add_edge("assistant", END)
    return graph.compile()


def generate_reply(message: str) -> str:
    prompt = (
        f"You are a helpful AI assistant for {settings.business_name}. "
        "Answer the user's questions directly and clearly using your language model. "
        "Be accurate and acknowledge uncertainty. Do not invent business-specific "
        "facts, policies, prices, or services that were not provided."
    )
    result = get_agent().invoke(
        {"messages": [SystemMessage(content=prompt), HumanMessage(content=message)]}
    )
    content = result["messages"][-1].content
    if isinstance(content, str):
        reply = content
    elif isinstance(content, list):
        reply = "".join(
            block["text"]
            for block in content
            if isinstance(block, dict)
            and block.get("type") == "text"
            and isinstance(block.get("text"), str)
        )
    else:
        reply = ""

    if not reply.strip():
        raise RuntimeError("The Gemini agent returned an empty or unsupported response.")
    return reply.strip()
