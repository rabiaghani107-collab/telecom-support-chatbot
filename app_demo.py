"""
TelcoBot Demo — Simulated version for screenshots and demo video.
Uses pre-scripted responses to showcase all features without requiring an API key.
"""

import uuid
import time
import gradio as gr
from data.database import initialize_database

# Initialize database for real tool calls
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
initialize_database()

# Import real tools to get actual data
from tools.billing import get_bill_details, get_payment_history, get_outstanding_balance
from tools.plans import list_available_plans, get_plan_details, compare_plans
from tools.usage import get_usage_summary, get_daily_usage
from tools.account import get_customer_profile, lookup_customer_by_name, create_support_ticket, get_open_tickets

APP_TITLE = "TelcoBot — AI Customer Support Assistant"
APP_DESCRIPTION = "Intelligent customer support for TelcoMax powered by LangChain & LangGraph"

# Pre-scripted conversation flows for demo
SCRIPTED_RESPONSES = {}

def get_real_tool_data(tool_func, **kwargs):
    """Call a real tool and get its output."""
    try:
        result = tool_func.invoke(kwargs)
        return result
    except Exception as e:
        return f"Error: {e}"

def generate_response(user_message: str, history: list) -> str:
    """Generate a realistic response based on the user message."""
    msg = user_message.lower().strip()
    
    # Greeting
    if any(w in msg for w in ["hi", "hello", "hey", "good morning", "good afternoon"]):
        return ("Hello! 👋 Welcome to **TelcoMax Customer Support**! I'm TelcoBot, your AI assistant.\n\n"
                "I can help you with:\n"
                "- 💰 **Billing** — bills, payments, balances\n"
                "- 📱 **Plans** — available plans, comparisons, upgrades\n"
                "- 🔧 **Technical Support** — troubleshooting connectivity issues\n"
                "- 📊 **Usage Tracking** — data, calls, and SMS usage\n"
                "- 👤 **Account Management** — profile info, support tickets\n\n"
                "How can I help you today?")
    
    # Bill inquiry
    if "bill" in msg and ("cust-1001" in msg or "alice" in msg or "1001" in msg):
        bill_data = get_real_tool_data(get_bill_details, customer_id="CUST-1001")
        return (f"I've looked up the billing information for customer **CUST-1001 (Alice Johnson)**. "
                f"Here are the details:\n\n"
                f"```\n{bill_data}\n```\n\n"
                f"🔧 **Tool Used:** `get_bill_details` → Routed via **Billing Agent**\n\n"
                f"Would you like to see the payment history or check for any outstanding balance?")
    
    if "bill" in msg and "1002" in msg:
        bill_data = get_real_tool_data(get_bill_details, customer_id="CUST-1002")
        return (f"Here are the billing details for **CUST-1002 (Bob Martinez)**:\n\n"
                f"```\n{bill_data}\n```\n\n"
                f"Is there anything else I can help with regarding this account?")
    
    if "bill" in msg or "charge" in msg or "invoice" in msg:
        return ("I'd be happy to help with your billing inquiry! 💰\n\n"
                "Could you please provide your **Customer ID**? "
                "Our sample customers are CUST-1001 through CUST-1006.\n\n"
                "🔧 **Intent Detected:** `billing` → Routed to **Billing Agent**")
    
    # Outstanding balance
    if "outstanding" in msg or "balance" in msg or "owe" in msg:
        if "1002" in msg:
            balance_data = get_real_tool_data(get_outstanding_balance, customer_id="CUST-1002")
            return (f"Here's the outstanding balance check for **CUST-1002**:\n\n"
                    f"```\n{balance_data}\n```\n\n"
                    f"🔧 **Tool Used:** `get_outstanding_balance` → **Billing Agent**")
        return ("I can check outstanding balances for you. Please provide your Customer ID.")
    
    # Payment history
    if "payment" in msg and "history" in msg:
        cust_id = "CUST-1001"
        for c in ["1001", "1002", "1003", "1004", "1005", "1006"]:
            if c in msg:
                cust_id = f"CUST-{c}"
                break
        history_data = get_real_tool_data(get_payment_history, customer_id=cust_id)
        return (f"Here's the payment history:\n\n"
                f"```\n{history_data}\n```\n\n"
                f"🔧 **Tool Used:** `get_payment_history` → **Billing Agent**")
    
    # Plans
    if "plan" in msg and ("offer" in msg or "available" in msg or "list" in msg or "what" in msg):
        plans_data = get_real_tool_data(list_available_plans)
        return (f"Here are all the plans we currently offer at TelcoMax:\n\n"
                f"```\n{plans_data}\n```\n\n"
                f"🔧 **Tool Used:** `list_available_plans` → Routed via **Plans Agent**\n\n"
                f"Would you like me to compare any of these plans or get more details on a specific one?")
    
    if "compare" in msg and "plan" in msg:
        compare_data = get_real_tool_data(compare_plans, plan_id_1="standard-02", plan_id_2="premium-03")
        return (f"Here's a comparison between the **Standard** and **Premium** plans:\n\n"
                f"```\n{compare_data}\n```\n\n"
                f"🔧 **Tool Used:** `compare_plans` → **Plans Agent**\n\n"
                f"The Premium plan offers significantly more data and features. Would you like to upgrade?")
    
    if "family" in msg and "plan" in msg:
        plan_data = get_real_tool_data(get_plan_details, plan_id="family-06")
        return (f"Here are the details for the **Family Plan**:\n\n"
                f"```\n{plan_data}\n```\n\n"
                f"🔧 **Tool Used:** `get_plan_details` → **Plans Agent**")
    
    # Technical support / slow internet
    if "slow" in msg or "internet" in msg or "speed" in msg or "connectivity" in msg or "network" in msg:
        return ("I understand you're experiencing **slow internet speeds**. Let me search our knowledge base for solutions.\n\n"
                "🔍 **RAG Knowledge Base Search Results:**\n\n"
                "Based on our troubleshooting guide, here are the recommended steps:\n\n"
                "1. **Restart your router** — Unplug for 30 seconds, then reconnect\n"
                "2. **Check for outages** — Visit telcomax.com/status for your area\n"
                "3. **Run a speed test** — Use speedtest.net to measure current speeds\n"
                "4. **Check connected devices** — Too many devices can slow your connection\n"
                "5. **Update router firmware** — Ensure your router has the latest firmware\n"
                "6. **Try a wired connection** — If on WiFi, test with an ethernet cable\n\n"
                "🔧 **Tool Used:** `search_knowledge_base` (RAG) → Routed via **Technical Agent**\n\n"
                "If the issue persists after these steps, I can create a support ticket for you. "
                "Would you like me to do that?")
    
    if "voicemail" in msg or "set up" in msg:
        return ("Great question! Here's how to **set up voicemail** on TelcoMax:\n\n"
                "🔍 **RAG Knowledge Base Search Results:**\n\n"
                "1. **Dial *86** from your TelcoMax phone\n"
                "2. Follow the automated prompts to create a **PIN** (4-6 digits)\n"
                "3. Record your **personal greeting**\n"
                "4. Press **#** to confirm and save\n\n"
                "**Additional tips:**\n"
                "- To check voicemail: Dial *86 or hold the 1 key\n"
                "- To change greeting: Dial *86 → Press 4 → Press 1\n"
                "- Visual voicemail is available on Premium and Unlimited plans\n\n"
                "🔧 **Tool Used:** `search_knowledge_base` (RAG) → **Technical Agent**")
    
    # Usage
    if "usage" in msg:
        cust_id = "CUST-1001"
        for c in ["1001", "1002", "1003", "1004", "1005", "1006"]:
            if c in msg:
                cust_id = f"CUST-{c}"
                break
        usage_data = get_real_tool_data(get_usage_summary, customer_id=cust_id)
        return (f"Here's the usage summary:\n\n"
                f"```\n{usage_data}\n```\n\n"
                f"🔧 **Tool Used:** `get_usage_summary` → Routed via **Usage Agent**\n\n"
                f"Would you like to see the daily breakdown?")
    
    # Account / customer lookup
    if "look up" in msg or "lookup" in msg or "find" in msg:
        if "alice" in msg:
            lookup_data = get_real_tool_data(lookup_customer_by_name, name="Alice")
            return (f"I found the following customer:\n\n"
                    f"```\n{lookup_data}\n```\n\n"
                    f"🔧 **Tool Used:** `lookup_customer_by_name` → **Account Agent**")
        return "I can look up a customer by name. Who would you like me to search for?"
    
    if "profile" in msg or "account" in msg or "customer" in msg:
        cust_id = "CUST-1001"
        for c in ["1001", "1002", "1003", "1004", "1005", "1006"]:
            if c in msg:
                cust_id = f"CUST-{c}"
                break
        profile_data = get_real_tool_data(get_customer_profile, customer_id=cust_id)
        return (f"Here's the customer profile:\n\n"
                f"```\n{profile_data}\n```\n\n"
                f"🔧 **Tool Used:** `get_customer_profile` → **Account Agent**")
    
    # Support ticket
    if "ticket" in msg or "create" in msg:
        if "cust" in msg:
            cust_id = "CUST-1003"
            for c in ["1001", "1002", "1003", "1004", "1005", "1006"]:
                if c in msg:
                    cust_id = f"CUST-{c}"
                    break
            ticket_data = get_real_tool_data(create_support_ticket, 
                                             customer_id=cust_id,
                                             category="technical",
                                             description="Customer reported slow internet speeds")
            return (f"I've created a support ticket:\n\n"
                    f"```\n{ticket_data}\n```\n\n"
                    f"🔧 **Tool Used:** `create_support_ticket` → **Account Agent**\n\n"
                    f"Our technical team will review this and get back to you within 24 hours.")
        return "I can create a support ticket. Please provide your Customer ID and describe the issue."
    
    # Follow-up / memory demonstration
    if "yes" in msg and "daily" in msg:
        daily_data = get_real_tool_data(get_daily_usage, customer_id="CUST-1001")
        return (f"Here's the daily usage breakdown:\n\n"
                f"```\n{daily_data}\n```\n\n"
                f"🔧 **Tool Used:** `get_daily_usage` → **Usage Agent**\n\n"
                f"📝 **Memory:** I remembered we were discussing CUST-1001's usage from our previous conversation!")
    
    if "yes" in msg or "sure" in msg or "please" in msg:
        # Context-aware follow-up based on history
        if history:
            last_bot = history[-1][1] if history[-1][1] else ""
            if "payment history" in last_bot.lower() or "bill" in last_bot.lower():
                ph_data = get_real_tool_data(get_payment_history, customer_id="CUST-1001")
                return (f"Sure! Here's the payment history for the account we were discussing:\n\n"
                        f"```\n{ph_data}\n```\n\n"
                        f"📝 **Memory in action:** I remembered the customer from our previous exchange!\n\n"
                        f"🔧 **Tool Used:** `get_payment_history` → **Billing Agent**")
            if "ticket" in last_bot.lower() or "support" in last_bot.lower():
                ticket_data = get_real_tool_data(create_support_ticket,
                                                 customer_id="CUST-1001",
                                                 category="technical",
                                                 description="Slow internet speeds reported by customer")
                return (f"I've created a support ticket for you:\n\n"
                        f"```\n{ticket_data}\n```\n\n"
                        f"📝 **Memory in action:** I used the context from our conversation to create this ticket!\n\n"
                        f"🔧 **Tool Used:** `create_support_ticket` → **Account Agent**")
    
    if "thank" in msg:
        return ("You're welcome! 😊 I'm glad I could help.\n\n"
                "Here's a summary of what we covered today:\n"
                "- Checked billing information\n"
                "- Reviewed available plans\n"
                "- Provided technical troubleshooting\n"
                "- Tracked usage data\n\n"
                "If you need anything else, don't hesitate to ask. Have a great day! 🌟\n\n"
                "📝 **Memory:** Full conversation context was maintained throughout our interaction.")
    
    # Default
    return ("I'd be happy to help! I can assist you with:\n\n"
            "- **Billing** — Check bills, payments, balances\n"
            "- **Plans** — View and compare plans\n"
            "- **Technical Support** — Troubleshoot issues\n"
            "- **Usage** — Track your data, calls, SMS\n"
            "- **Account** — Profile info, support tickets\n\n"
            "What would you like help with?")


def chat(user_message: str, history: list, session_id: str) -> tuple:
    """Process user message and return response."""
    if not user_message.strip():
        return history, ""
    
    # Convert history to old format for generate_response
    old_history = []
    i = 0
    while i < len(history):
        if history[i].get("role") == "user":
            user_msg = history[i].get("content", "")
            assistant_msg = ""
            if i + 1 < len(history) and history[i+1].get("role") == "assistant":
                assistant_msg = history[i+1].get("content", "")
                i += 1
            old_history.append([user_msg, assistant_msg])
        i += 1
    
    response = generate_response(user_message, old_history)
    history = history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": response},
    ]
    return history, ""


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
    with gr.Blocks(title=APP_TITLE) as demo:
        gr.Markdown(f"# 📡 {APP_TITLE}")
        gr.Markdown(f"*{APP_DESCRIPTION}*")
        gr.Markdown(
            "I can help you with **billing**, **plans**, **technical support**, "
            "**usage tracking**, and **account management**."
        )

        session_id = gr.State(value=lambda: str(uuid.uuid4()))

        chatbot = gr.Chatbot(
            label="Chat",
            height=480,
        )

        with gr.Row():
            msg = gr.Textbox(
                placeholder="Type your message here …",
                show_label=False,
                scale=9,
                container=False,
            )
            send_btn = gr.Button("Send", variant="primary", scale=1)

        gr.Examples(
            examples=EXAMPLE_PROMPTS,
            inputs=msg,
            label="💡 Try these example prompts",
        )

        clear_btn = gr.Button("🗑️ Clear Chat")

        send_btn.click(chat, [msg, chatbot, session_id], [chatbot, msg])
        msg.submit(chat, [msg, chatbot, session_id], [chatbot, msg])
        clear_btn.click(
            lambda: ([], str(uuid.uuid4())),
            outputs=[chatbot, session_id],
        )

        gr.Markdown(
            "---\n"
            "Built with **LangChain** 🦜🔗 • **LangGraph** 🕸️ • **Gradio** 🎨 • **ChromaDB** 💎 • **SQLite** 🗄️\n\n"
            "⚠️ *This is a demo chatbot. Use sample customer IDs: CUST-1001 through CUST-1006.*"
        )

    return demo


if __name__ == "__main__":
    print("🚀 Starting TelcoBot Demo...")
    initialize_database()
    print("✅ Database initialized.")
    demo = create_interface()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
