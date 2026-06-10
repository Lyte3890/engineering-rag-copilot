from typing import Optional
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from pydantic import SecretStr
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("CRITICAL ERROR: GROQ_API_KEY not found in .env file")

embeddings = HuggingFaceEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")
CHROMA_PATH = "chroma_db"
DOCS_DIR = "docs_storage"

def reset_database():
    """Hard reset of the vector database to prevent chunk duplication."""
    if os.path.exists(CHROMA_PATH):
        print("[*] Wiping existing vector database...")
        shutil.rmtree(CHROMA_PATH)

def process_document(pdf_path: str):
    """Parses a single PDF and appends to the vector database."""
    print(f"[*] Loading document: {pdf_path}")
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)

    Chroma.from_documents(chunks, embeddings, persist_directory=CHROMA_PATH)
    return len(chunks)

def sync_directory():
    """Wipes the DB and rebuilds it from all PDFs currently in DOCS_DIR."""
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)
        return 0, 0

    pdf_files = glob.glob(os.path.join(DOCS_DIR, "*.pdf"))
    if not pdf_files:
        return 0, 0

    reset_database()
    
    total_chunks = 0
    for pdf in pdf_files:
        total_chunks += process_document(pdf)
        
    return len(pdf_files), total_chunks

def format_chat_history(history_list: list) -> list[BaseMessage]:
    formatted_history: list[BaseMessage] = []
    for msg in history_list:
        if msg.get("role") == "user":
            formatted_history.append(HumanMessage(content=msg.get("content")))
        elif msg.get("role") == "assistant":
            formatted_history.append(AIMessage(content=msg.get("content")))
    return formatted_history


def ask_engineering_question(query: str, chat_history: Optional[list] = None):
    if not os.path.exists(CHROMA_PATH):
        return {"answer": "Database is empty. Please upload or sync documentation first.", "sources": []}

    if chat_history is None:
        chat_history = []

    formatted_history = format_chat_history(chat_history)

    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
    retriever = db.as_retriever(search_kwargs={"k": 5})

    llm = ChatGroq(
        api_key=SecretStr(str(GROQ_API_KEY)),
        model="llama-3.3-70b-versatile",
        temperature=0.1
    )
    # ... (решта коду функції залишається без змін)
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    qa_system_prompt = (
        "You are an expert hardware engineering assistant. Use the following pieces of retrieved context "
        "to answer the question. "
        "CRITICAL INSTRUCTIONS: "
        "1. When asked about specific hardware components, ALWAYS list exact identifiers (e.g., pin numbers, register names, voltage limits) if they exist in the context. "
        "2. Do NOT summarize or generalize data if specific details are available. "
        "3. If the context does not contain the specific answer, explicitly state: 'The provided documentation does not specify this.' "
        "4. Be precise and structured.\n\n"
        "Context: {context}"
    )
    
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    response = rag_chain.invoke({
        "input": query,
        "chat_history": formatted_history
    })
    
    sources = []
    for doc in response["context"]:
        source_path = doc.metadata.get("source", "")
        file_name = os.path.basename(source_path) if source_path else "Unknown source"
        
        raw_page = doc.metadata.get("page")
        page = int(raw_page) + 1 if raw_page is not None else "N/A"
        
        sources.append({"file": file_name, "page": page})

    unique_sources = [dict(t) for t in {tuple(d.items()) for d in sources}]

    return {
        "answer": response["answer"],
        "sources": unique_sources
    }
