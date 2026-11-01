from typing import TypedDict, Any
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings
from app.vectorstore import get_vectorstore

class RAGState(TypedDict, total=False):
    question: str
    rewritten_query: str
    query_type: str
    documents: list
    relevant_documents: list
    answer: str
    retries: int
    max_retries: int
    sources: list[dict]
    status: str

def _llm() -> ChatGoogleGenerativeAI:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it to your .env file.")
    return ChatGoogleGenerativeAI(
        model=settings.chat_model,
        temperature=0,
        google_api_key=settings.gemini_api_key,
    )

def query_analysis(state: RAGState) -> dict:
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You improve search queries for technical documentation. "
         "Return only one concise search query. Preserve the user's intent. "
         "Add relevant technical synonyms only when useful."),
        ("human", "Question: {question}\nPrevious query: {previous}")
    ])
    result = (prompt | _llm()).invoke({
        "question": state["question"],
        "previous": state.get("rewritten_query", ""),
    })
    query = result.content if isinstance(result.content, str) else str(result.content)
    return {"rewritten_query": query.strip() or state["question"]}

def retrieval(state: RAGState) -> dict:
    store = get_vectorstore()
    query = state.get("rewritten_query") or state["question"]
    docs = store.similarity_search(query, k=settings.retrieval_k)
    return {"documents": docs}

def document_grading(state: RAGState) -> dict:
    docs = state.get("documents", [])
    if not docs:
        return {"relevant_documents": []}
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a strict relevance evaluator for a technical documentation assistant. "
         "Decide whether the passage contains information useful for answering the question. "
         "Reply with exactly YES or NO. Do not use outside knowledge."),
        ("human", "Question: {question}\n\nPassage:\n{passage}")
    ])
    chain = prompt | _llm()
    relevant = []
    for doc in docs:
        try:
            result = chain.invoke({
                "question": state["question"],
                "passage": doc.page_content[:5000],
            })
            verdict = str(result.content).strip().upper()
            if verdict.startswith("YES"):
                relevant.append(doc)
        except Exception:
            # Fail closed: uncertain grading must not be treated as relevant.
            continue
    return {"relevant_documents": relevant}

def route_after_grading(state: RAGState) -> str:
    if state.get("relevant_documents"):
        return "generate"
    if state.get("retries", 0) < state.get("max_retries", settings.max_retries):
        return "rewrite"
    return "no_answer"

def generate_answer(state: RAGState) -> dict:
    context_parts = []
    sources = []
    for i, doc in enumerate(state.get("relevant_documents", []), start=1):
        source = doc.metadata.get("source", "unknown")
        context_parts.append(f"[{i}] Source: {source}\n{doc.page_content}")
        sources.append({
            "citation": f"[{i}]",
            "source": source,
            "source_type": doc.metadata.get("source_type", "unknown"),
        })
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a careful technical documentation assistant. Answer using ONLY "
         "the supplied context. Cite factual claims with [1], [2], etc. "
         "If the context does not fully support an answer, say what is missing. "
         "Do not invent APIs, parameters, versions, or behavior."),
        ("human", "Question: {question}\n\nContext:\n{context}")
    ])
    result = (prompt | _llm()).invoke({
        "question": state["question"],
        "context": "\n\n---\n\n".join(context_parts),
    })
    answer = result.content if isinstance(result.content, str) else str(result.content)
    return {"answer": answer, "sources": sources, "status": "answered"}

def no_answer(state: RAGState) -> dict:
    return {
        "answer": (
            "I could not find sufficiently relevant information in the indexed "
            "documentation to answer this question reliably. Try rephrasing the "
            "question or ingesting the relevant documentation."
        ),
        "sources": [],
        "status": "insufficient_context",
    }

def increment_retry(state: RAGState) -> dict:
    return {"retries": state.get("retries", 0) + 1, "documents": [], "relevant_documents": []}

def build_graph():
    graph = StateGraph(RAGState)
    graph.add_node("query_analysis", query_analysis)
    graph.add_node("retrieval", retrieval)
    graph.add_node("document_grading", document_grading)
    graph.add_node("generate", generate_answer)
    graph.add_node("no_answer", no_answer)
    graph.add_node("retry", increment_retry)

    graph.set_entry_point("query_analysis")
    graph.add_edge("query_analysis", "retrieval")
    graph.add_edge("retrieval", "document_grading")
    graph.add_conditional_edges(
        "document_grading",
        route_after_grading,
        {"generate": "generate", "rewrite": "retry", "no_answer": "no_answer"},
    )
    graph.add_edge("retry", "query_analysis")
    graph.add_edge("generate", END)
    graph.add_edge("no_answer", END)
    return graph.compile()

rag_graph = build_graph()

def answer_question(question: str) -> dict:
    result = rag_graph.invoke({
        "question": question,
        "retries": 0,
        "max_retries": settings.max_retries,
        "sources": [],
    })
    return {
        "answer": result.get("answer", ""),
        "sources": result.get("sources", []),
        "retries": result.get("retries", 0),
        "status": result.get("status", "unknown"),
    }
