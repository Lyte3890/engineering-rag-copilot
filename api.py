from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

@app.post("/api/chat")
async def chat_endpoint(
    query: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    model: str = Form("llama-3.3-70b-versatile")
):
    response_text = ""
    sources_list = []

    # 1. Обробка файлу
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

    # 2. Обробка запиту
    if query:
        try:
            rag_result = ask_engineering_question(query, [], model_name=model)
            
            if isinstance(rag_result, dict):
                response_text += rag_result.get("answer", "")
                # rag_core.py вже правильно формує джерела як {"doc": "...", "page": "..."}
                sources_list = rag_result.get("sources", [])
            else:
                response_text += str(rag_result)

        except Exception as e:
            print(f"RAG Error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"API Error: {str(e)}")

    if not query and not file:
        raise HTTPException(status_code=400, detail="Empty request: provide text or PDF.")

    return {
        "text": response_text.strip(),
        "sources": sources_list
    }

# Додаткові системні ендпоінти
class QueryRequest(BaseModel):
    query: str
    chat_history: Optional[List[Dict[str, str]]] = []

@app.post("/ask")
async def ask_question(request: QueryRequest):
    try:
        return ask_engineering_question(request.query, request.chat_history)
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
        return {"message": f"Successfully uploaded '{file.filename}' ({chunks_count} chunks)."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync")
async def sync_storage_directory():
    try:
        files_count, chunks_count = sync_directory()
        return {"message": f"Storage synchronized. Indexed {files_count} files ({chunks_count} chunks)."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)