from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from rag_core import ask_engineering_question, process_document, sync_directory, DOCS_DIR
import os
import shutil

app = FastAPI(title="Engineering RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(DOCS_DIR, exist_ok=True)
app.mount("/docs", StaticFiles(directory=DOCS_DIR), name="docs")

class QueryRequest(BaseModel):
    query: str
    chat_history: Optional[List[Dict[str, str]]] = []

class ProcessRequest(BaseModel):
    file_path: str

@app.post("/ask")
async def ask_question(request: QueryRequest):
    try:
        result = ask_engineering_question(request.query, request.chat_history)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_and_process_pdf(file: UploadFile = File(...)):
    if file.filename is None or not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_path = os.path.join(DOCS_DIR, file.filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        chunks_count = process_document(file_path)
        return {"message": f"Successfully uploaded and indexed '{file.filename}' ({chunks_count} chunks)."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync")
async def sync_storage_directory():
    try:
        files_count, chunks_count = sync_directory()
        return {"message": f"Storage synchronized. Indexed {files_count} files ({chunks_count} chunks total)."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import os

@app.post("/api/chat")
async def chat_endpoint(
    query: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    model: str = Form("llama3-70b-8192")
):
    response_text = ""
    sources_list = []

    # 1. Process File
    if file:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
        file_path = os.path.join(DOCS_DIR, file.filename)
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            chunks_count = process_document(file_path)
            response_text += f"✅ File '{file.filename}' processed & vectorized ({chunks_count} chunks).\n\n"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File processing error: {str(e)}")

    # 2. Process Query
    if query:
        try:
            rag_result = ask_engineering_question(query, [])
            
            if isinstance(rag_result, dict):
                response_text += rag_result.get("answer", "")
                raw_sources = rag_result.get("sources", [])
                
                # --- BULLETPROOF METADATA EXTRACTION ---
                for src in raw_sources:
                    doc_name = "unknown.pdf"
                    page_num = "1"
                    
                    # Case A: LangChain Document object
                    if hasattr(src, "metadata") and isinstance(src.metadata, dict):
                        meta = src.metadata
                        # Checking all possible keys LangChain might use
                        raw_path = meta.get("source", meta.get("file_path", meta.get("file", "")))
                        page_num = meta.get("page", meta.get("page_label", meta.get("page_number", "1")))
                        if raw_path:
                            doc_name = os.path.basename(str(raw_path))
                            
                    # Case B: Dictionary object
                    elif isinstance(src, dict):
                        meta = src.get("metadata", src)
                        if isinstance(meta, dict):
                            raw_path = meta.get("source", meta.get("file_path", meta.get("document_name", "")))
                            page_num = meta.get("page", meta.get("page_label", "1"))
                            if raw_path:
                                doc_name = os.path.basename(str(raw_path))
                    
                    sources_list.append({
                        "doc": doc_name,
                        "page": str(page_num)
                    })
            else:
                response_text += str(rag_result)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"RAG query error: {str(e)}")

    if not query and not file:
        raise HTTPException(status_code=400, detail="Empty request: provide text or PDF.")

    return {
        "text": response_text.strip(),
        "sources": sources_list
    }
    response_text = ""
    sources_list = []

    # 1. Обробка файлу (якщо користувач його прикріпив)
    if file:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
        file_path = os.path.join(DOCS_DIR, file.filename)
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Використовуємо твою існуючу функцію з rag_core
            chunks_count = process_document(file_path)
            response_text += f"✅ File '{file.filename}' processed & vectorized ({chunks_count} chunks).\n\n"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File processing error: {str(e)}")

    # 2. Обробка текстового запиту (якщо користувач його написав)
    if query:
        try:
            # Викликаємо твою RAG функцію
            rag_result = ask_engineering_question(query, [])
            
            # Адаптуємо результат під формат React
            if isinstance(rag_result, dict):
                response_text += rag_result.get("answer", "")
                sources_list = rag_result.get("sources", [])
            else:
                # Якщо функція повертає просто строку
                response_text += str(rag_result)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"RAG query error: {str(e)}")

    # 3. Перевірка на порожній запит
    if not query and not file:
        raise HTTPException(status_code=400, detail="Empty request: provide text or PDF.")

    # 4. Повертаємо JSON у тому форматі, який очікує React-фронтенд
    return {
        "text": response_text.strip(),
        "sources": sources_list
    }    

if __name__ == "__main__":
    import uvicorn
    # 0.0.0.0 означає, що сервер слухає запити з УСІХ мережевих інтерфейсів (LAN)
    uvicorn.run(app, host="0.0.0.0", port=8000)
