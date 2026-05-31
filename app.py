"""
TelcoBot — AI-powered Customer Support Chatbot for TelcoMax
Main application entry point with Gradio UI.

Features:
  • LangGraph workflow with conditional routing
  • Multi-turn conversational memory
  • RAG-powered knowledge base search
  • SQLite-backed customer data
  • Streaming responses via Gradio
  • LangSmith tracing (optional)
"""

import uuid
import gradio as gr
from langchain_core.messages import HumanMessage, AIMessage

from config.settings import APP_TITLE, APP_DESCRIPTION, LANGSMITH_TRACING
from data.database import initialize_database
from tools.rag import build_vectorstore, get_retriever
from tools.tech_support import set_retriever
from agents.graph import build_graph


# ═════════════════════════════════════════════════════════════════════
# Application Initialisation
# ═════════════════════════════════════════════════════════════════════

def initialize_app():
    """One-time setup: database, vector store, graph."""
    print("🚀 Initializing TelcoBot …")

    # 1. Database
    print("  📦 Setting up SQLite database …")
    initialize_database()

    # 2. RAG vector store
    print("  🧠 Setting up RAG knowledge base …")
    try:
        vectorstore = build_vectorstore()
        retriever = get_retriever(vectorstore)
        set_retriever(retriever)
        print("  ✅ RAG knowledge base ready.")
    except Exception as e:
        print(f"  ⚠️  RAG setup failed ({e}). Knowledge base search will be unavailable.")

    # 3. LangGraph workflow
    print("  🔧 Building LangGraph workflow …")
    graph = build_graph()
    print("  ✅ Workflow compiled.")

    if LANGSMITH_TRACING:
        print("  📊 LangSmith tracing is ENABLED.")

    print("✅ TelcoBot is ready!\n")
    return graph


# Build the graph once at module level
graph = initialize_app()


# ═════════════════════════════════════════════════════════════════════
# Chat Handler
# ═════════════════════════════════════════════════════════════════════

def chat(user_message: str, history: list, session_id: str) -> tuple:
    """Process a user message through the LangGraph workflow.

    Args:
        user_message: The latest user input.
        history: Gradio chat history (list of [user, assistant] pairs).
        session_id: Unique session identifier for memory.

    Returns:
        Updated history and empty string to clear the input box.
    """
    if not user_message.strip():
        return history, ""

    # Configuration for checkpointer (memory) — keyed by session
    config = {"configurable": {"thread_id": session_id}}

    # Invoke the graph
    result = graph.invoke(
        {"messages": [HumanMessage(content=user_message)], "intent": ""},
        config=config,
    )

    # Extract the last AI message from the result
    ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
    if ai_messages:
        response = ai_messages[-1].content
    else:
        response = "I'm sorry, I couldn't process your request. Could you please rephrase?"

    # Update Gradio history (Gradio 6 uses dict format)
    history = history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": response},
    ]
    return history, ""


# ═════════════════════════════════════════════════════════════════════
# Gradio Interface
# ═════════════════════════════════════════════════════════════════════

EXAMPLE_PROMPTS = [
    "Hi, I need help with my bill",
    "What plans do you offer?",
    "My internet is very slow, can you help?",
    "Show me the usage for customer CUST-1001",
    "Look up a customer named Alice",
    "Can you compare the Standard and Premium plans?",
    "What's the outstanding balance for CUST-1002?",
    "I want to create a support ticket for CUST-1003",
    "How do I set up voicemail?",
    "What's included in the Family plan?",
]

CSS = """
.gradio-container { max-width: 900px !important; margin: auto; }
footer { display: none !important; }
"""

def create_interface() -> gr.Blocks:
    """Build the Gradio Blocks UI."""
    with gr.Blocks(title=APP_TITLE) as demo:
        # Header
        gr.Markdown(f"# 📡 {APP_TITLE}")
        gr.Markdown(f"*{APP_DESCRIPTION}*")
        gr.Markdown(
            "I can help you with **billing**, **plans**, **technical support**, "
            "**usage tracking**, and **account management**."
        )

        # Session state
        session_id = gr.State(value=lambda: str(uuid.uuid4()))

        # Chat area
        chatbot = gr.Chatbot(
            label="Chat",
            height=480,
        )

        # Input row
        with gr.Row():
            msg = gr.Textbox(
                placeholder="Type your message here …",
                show_label=False,
                scale=9,
                container=False,
            )
            send_btn = gr.Button("Send", variant="primary", scale=1)

        # Example prompts
        gr.Examples(
            examples=EXAMPLE_PROMPTS,
            inputs=msg,
            label="💡 Try these example prompts",
        )

        # Clear button
        clear_btn = gr.Button("🗑️ Clear Chat")

        # Wire events
        send_btn.click(chat, [msg, chatbot, session_id], [chatbot, msg])
        msg.submit(chat, [msg, chatbot, session_id], [chatbot, msg])
        clear_btn.click(
            lambda: ([], str(uuid.uuid4())),
            outputs=[chatbot, session_id],
        )

        # Footer
        gr.Markdown(
            "---\n"
            "Built with **LangChain** 🦜🔗 • **LangGraph** 🕸️ • **Gradio** 🎨 • **ChromaDB** 💎 • **SQLite** 🗄️\n\n"
            "⚠️ *This is a demo chatbot. Use sample customer IDs: CUST-1001 through CUST-1006.*"
        )

    return demo


# ═════════════════════════════════════════════════════════════════════
# Entry Point
# ═════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
