import logging
import re
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_groq import ChatGroq
import numexpr

from app.core.config import get_settings
from app.services.ingestion import get_chroma_client, get_embeddings

logger = logging.getLogger(__name__)
settings = get_settings()


def get_llm() -> ChatGroq:
    return ChatGroq(
        model=settings.model_name,
        api_key=settings.groq_api_key,
        temperature=0.1,
        max_retries=2,
    )


@tool
def retrieval_tool(query: str) -> str:
    """
    Recherche dans les documents uploadés les passages pertinents
    pour répondre à la question. Retourne les chunks avec leurs sources.
    Utilise cet outil pour toute question sur le contenu des documents.
    """
    client = get_chroma_client()
    embeddings_model = get_embeddings()

    try:
        collection = client.get_collection("documents")
    except Exception:
        return "Aucun document uploadé. Veuillez d'abord uploader un document."

    query_embedding = embeddings_model.embed_query(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=settings.retrieval_k,
        include=["documents", "metadatas", "distances"],
    )

    if not results["documents"][0]:
        return "Aucun passage pertinent trouvé dans les documents."

    formatted = []
    for i, (doc, meta, dist) in enumerate(
        zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ):
        source = meta.get("source", "inconnu")
        page = meta.get("page", "?")
        relevance = round((1 - dist) * 100, 1)
        formatted.append(
            f"[Source {i+1}: {source}, page {page}, pertinence {relevance}%]\n{doc}"
        )

    return "\n\n---\n\n".join(formatted)


@tool
def calculator_tool(expression: str) -> str:
    """
    Effectue des calculs mathématiques.
    Utilise cet outil quand la question demande un calcul numérique.
    Exemple : '15 * 1.2 + 300', '2 ** 10'
    """
    try:
        result = numexpr.evaluate(expression)
        return f"Résultat : {result}"
    except Exception as e:
        return f"Erreur de calcul : {str(e)}"


@tool
def summarize_tool(filename: str) -> str:
    """
    Génère un résumé structuré d'un document spécifique.
    Utilise cet outil quand l'utilisateur demande explicitement
    un résumé d'un document par son nom.
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection("documents")
    except Exception:
        return "Aucun document trouvé."

    results = collection.get(
        where={"source": filename},
        include=["documents"],
        limit=20,
    )

    if not results["documents"]:
        return f"Document '{filename}' non trouvé."

    content = "\n\n".join(results["documents"][:15])
    llm = get_llm()
    response = llm.invoke(
        f"Génère un résumé structuré en 5-8 points clés du document '{filename}':\n\n{content}"
    )
    return response.content


SYSTEM_PROMPT = """Tu es un assistant expert en analyse de documents.
Tu as accès à des outils pour répondre aux questions.

Règles importantes :
- Utilise TOUJOURS retrieval_tool avant de répondre à une question sur les documents
- Si la réponse n'est pas dans les documents, dis-le clairement
- Cite toujours tes sources avec [Source X: nom_fichier, page Y]
- Utilise calculator_tool uniquement pour les calculs numériques
- Utilise summarize_tool quand on te demande explicitement un résumé
- Réponds en français sauf si l'utilisateur écrit dans une autre langue
"""

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder("chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])


def create_agent_executor() -> AgentExecutor:
    llm = get_llm()
    tools = [retrieval_tool, calculator_tool, summarize_tool]
    agent = create_tool_calling_agent(llm, tools, PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=5,
        return_intermediate_steps=True,
    )


def run_agent(question: str, chat_history: list = None) -> dict:
    executor = create_agent_executor()
    result = executor.invoke({
        "input": question,
        "chat_history": chat_history or [],
    })

    sources = []
    for step in result.get("intermediate_steps", []):
        tool_output = step[1] if len(step) > 1 else ""
        if "[Source" in str(tool_output):
            import re
            found = re.findall(
                r'\[Source \d+: ([^,]+), page ([^\]]+)',
                str(tool_output)
            )
            for fname, page in found:
                source = {"filename": fname.strip(), "page": page.strip()}
                if source not in sources:
                    sources.append(source)

    return {
        "answer": result["output"],
        "sources": sources,
    }