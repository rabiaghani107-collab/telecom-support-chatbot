"""
LangGraph Workflow — the core agentic pipeline.

Architecture:
  ┌─────────┐     ┌─────────────┐     ┌────────────┐
  │  START   │────▶│  Classifier │────▶│  Router    │
  └─────────┘     └─────────────┘     └────┬───────┘
                                           │ (conditional edge)
                    ┌──────────────────────┼──────────────────────┐
                    ▼                      ▼                      ▼
            ┌──────────────┐     ┌──────────────┐      ┌──────────────┐
            │ Billing Agent│     │ Tech  Agent  │      │Account Agent │
            └──────┬───────┘     └──────┬───────┘      └──────┬───────┘
                   │                    │                      │
                   └──────────┬─────────┘──────────────────────┘
                              ▼
                       ┌─────────────┐
                       │  Responder  │
                       └──────┬──────┘
                              ▼
                          ┌───────┐
                          │  END  │
                          └───────┘

Each specialised agent has access to its own subset of tools.
The Classifier determines the intent and the Router selects the right agent.
Memory is implemented via LangGraph's built-in checkpointer.
"""

from __future__ import annotations

import operator
from typing import Annotated, Sequence, TypedDict, Literal

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from config.settings import LLM_MODEL, LLM_TEMPERATURE

# ── Tool imports ──────────────────────────────────────────────────────
from tools.billing import get_bill_details, get_payment_history, get_outstanding_balance
from tools.plans import list_available_plans, get_plan_details, compare_plans
from tools.usage import get_usage_summary, get_daily_usage
from tools.account import (
    get_customer_profile,
    lookup_customer_by_name,
    create_support_ticket,
    get_open_tickets,
)
from tools.tech_support import search_knowledge_base


# ═════════════════════════════════════════════════════════════════════
# State definition — shared across all nodes
# ═════════════════════════════════════════════════════════════════════

class AgentState(TypedDict):
    """Shared state that flows through the graph."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    intent: str  # detected intent category


# ═════════════════════════════════════════════════════════════════════
# Tool groups
# ═════════════════════════════════════════════════════════════════════

BILLING_TOOLS = [get_bill_details, get_payment_history, get_outstanding_balance]
PLAN_TOOLS = [list_available_plans, get_plan_details, compare_plans]
USAGE_TOOLS = [get_usage_summary, get_daily_usage]
ACCOUNT_TOOLS = [get_customer_profile, lookup_customer_by_name, create_support_ticket, get_open_tickets]
TECH_TOOLS = [search_knowledge_base]

ALL_TOOLS = BILLING_TOOLS + PLAN_TOOLS + USAGE_TOOLS + ACCOUNT_TOOLS + TECH_TOOLS


# ═════════════════════════════════════════════════════════════════════
# Node functions
# ═════════════════════════════════════════════════════════════════════

def _get_llm(**kwargs):
    return ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE, streaming=True, **kwargs)


# ── 1. Intent Classifier ──────────────────────────────────────────────

CLASSIFIER_PROMPT = """You are an intent classifier for TelcoMax customer support.
Classify the customer's latest message into EXACTLY one of these categories:

- billing    : questions about bills, payments, charges, invoices, balance
- plans      : questions about available plans, plan features, upgrades, downgrades, comparisons
- technical  : troubleshooting, network issues, device problems, signal, speed, connectivity
- usage      : data usage, call minutes, SMS count, consumption tracking
- account    : profile info, account status, name lookup, support tickets
- general    : greetings, thanks, anything that doesn't fit above

Respond with ONLY the category name, nothing else."""


def classify_intent(state: AgentState) -> dict:
    """Classify the user's intent from the latest message."""
    llm = _get_llm()
    messages = [
        SystemMessage(content=CLASSIFIER_PROMPT),
        HumanMessage(content=state["messages"][-1].content),
    ]
    result = llm.invoke(messages)
    intent = result.content.strip().lower()
    # Normalise to known categories
    valid = {"billing", "plans", "technical", "usage", "account", "general"}
    if intent not in valid:
        intent = "general"
    return {"intent": intent}


# ── 2. Specialised Agent Nodes ────────────────────────────────────────

def _make_agent_node(name: str, tools: list, system_prompt: str):
    """Factory that builds a node function for a specialised agent."""
    def agent_node(state: AgentState) -> dict:
        llm = _get_llm().bind_tools(tools)
        sys_msg = SystemMessage(content=system_prompt)
        # Include full conversation for context (memory)
        messages = [sys_msg] + list(state["messages"])
        response = llm.invoke(messages)
        return {"messages": [response]}
    agent_node.__name__ = name  # LangGraph uses __name__
    return agent_node


billing_agent = _make_agent_node(
    "billing_agent",
    BILLING_TOOLS,
    "You are a billing specialist at TelcoMax. Help customers with bill inquiries, "
    "payment history, and outstanding balances. Always be polite and precise with dollar amounts. "
    "Use the provided tools to fetch real data. If you need a customer ID, ask for it."
)

plans_agent = _make_agent_node(
    "plans_agent",
    PLAN_TOOLS,
    "You are a plan advisor at TelcoMax. Help customers find the right plan, "
    "compare options, and understand plan features. Recommend plans based on usage patterns. "
    "Use tools to get accurate plan information."
)

technical_agent = _make_agent_node(
    "technical_agent",
    TECH_TOOLS,
    "You are a technical support specialist at TelcoMax. Help customers troubleshoot "
    "network, device, and connectivity issues. Search the knowledge base for solutions. "
    "Provide step-by-step instructions when possible."
)

usage_agent = _make_agent_node(
    "usage_agent",
    USAGE_TOOLS,
    "You are a usage analyst at TelcoMax. Help customers understand their data, "
    "call, and SMS consumption. Provide insights and warn about approaching limits. "
    "Use tools to fetch real usage data."
)

account_agent = _make_agent_node(
    "account_agent",
    ACCOUNT_TOOLS,
    "You are an account manager at TelcoMax. Help customers view their profile, "
    "look up accounts, and manage support tickets. Ensure customer data privacy. "
    "Use tools to access account information."
)

def general_agent(state: AgentState) -> dict:
    """Handle greetings, small-talk, and off-topic queries."""
    llm = _get_llm()
    sys_msg = SystemMessage(
        content=(
            "You are TelcoBot, the friendly AI assistant for TelcoMax telecom. "
            "Greet the customer warmly and offer to help with billing, plans, "
            "technical support, usage tracking, or account management. "
            "Keep responses concise and helpful."
        )
    )
    messages = [sys_msg] + list(state["messages"])
    response = llm.invoke(messages)
    return {"messages": [response]}


# ── 3. Tool Executor Node ────────────────────────────────────────────

tool_node = ToolNode(ALL_TOOLS)


# ── 4. Response Synthesiser ───────────────────────────────────────────

def should_continue(state: AgentState) -> Literal["tools", "end"]:
    """After an agent runs, decide whether to call tools or finish."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "end"


# ── 5. Router — conditional edge from classifier ─────────────────────

def route_by_intent(state: AgentState) -> str:
    """Map intent string to the correct agent node name."""
    mapping = {
        "billing": "billing_agent",
        "plans": "plans_agent",
        "technical": "technical_agent",
        "usage": "usage_agent",
        "account": "account_agent",
        "general": "general_agent",
    }
    return mapping.get(state["intent"], "general_agent")


# ═════════════════════════════════════════════════════════════════════
# Graph Assembly
# ═════════════════════════════════════════════════════════════════════

def build_graph():
    """Construct and compile the LangGraph workflow with memory."""

    workflow = StateGraph(AgentState)

    # ── Add nodes ─────────────────────────────────────────────────
    workflow.add_node("classifier", classify_intent)
    workflow.add_node("billing_agent", billing_agent)
    workflow.add_node("plans_agent", plans_agent)
    workflow.add_node("technical_agent", technical_agent)
    workflow.add_node("usage_agent", usage_agent)
    workflow.add_node("account_agent", account_agent)
    workflow.add_node("general_agent", general_agent)
    workflow.add_node("tools", tool_node)

    # ── Entry point ───────────────────────────────────────────────
    workflow.set_entry_point("classifier")

    # ── Conditional routing from classifier to agents ─────────────
    workflow.add_conditional_edges(
        "classifier",
        route_by_intent,
        {
            "billing_agent": "billing_agent",
            "plans_agent": "plans_agent",
            "technical_agent": "technical_agent",
            "usage_agent": "usage_agent",
            "account_agent": "account_agent",
            "general_agent": "general_agent",
        },
    )

    # ── From each agent → decide: call tools or end ──────────────
    for agent_name in [
        "billing_agent", "plans_agent", "technical_agent",
        "usage_agent", "account_agent",
    ]:
        workflow.add_conditional_edges(
            agent_name,
            should_continue,
            {"tools": "tools", "end": END},
        )

    # General agent never uses tools → straight to END
    workflow.add_edge("general_agent", END)

    # ── After tool execution, go back to the same agent ──────────
    # We route back to the classifier which re-evaluates
    # (in practice the agent will now see the tool result and respond)
    workflow.add_conditional_edges(
        "tools",
        route_by_intent,  # re-route based on stored intent
        {
            "billing_agent": "billing_agent",
            "plans_agent": "plans_agent",
            "technical_agent": "technical_agent",
            "usage_agent": "usage_agent",
            "account_agent": "account_agent",
            "general_agent": "general_agent",
        },
    )

    # ── Memory — MemorySaver checkpointer for multi-turn ─────────
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)

    return graph
