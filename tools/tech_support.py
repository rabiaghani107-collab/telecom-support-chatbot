"""
Technical support tool — uses RAG retrieval over the knowledge base to answer
troubleshooting and policy questions.
"""

from langchain_core.tools import tool


# The retriever is injected at runtime by the agent builder so the tool
# itself stays free of heavy imports.
_retriever = None


def set_retriever(retriever):
    """Called once during app startup to wire the vector-store retriever."""
    global _retriever
    _retriever = retriever


@tool
def search_knowledge_base(query: str) -> str:
    """Search the TelcoMax knowledge base for troubleshooting steps, policies,
    or plan information.

    Args:
        query: Natural-language question (e.g. 'how to fix slow data speeds').

    Returns:
        Relevant knowledge-base excerpts.
    """
    if _retriever is None:
        return (
            "Knowledge base is not loaded. Please refer the customer to "
            "telcomax.com/support or call 1-800-TELCOMAX."
        )
    docs = _retriever.invoke(query)
    if not docs:
        return "No relevant articles found in the knowledge base."
    sections = ["📚 Knowledge Base Results:\n"]
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        sections.append(f"--- Result {i} (source: {source}) ---\n{doc.page_content}\n")
    return "\n".join(sections)
