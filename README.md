# doc-ai-assistant
A document-grounded AI assistant: a small full-stack app where a user can upload documents and have a conversation with an agent that answers questions using those documents as its source of truth.
# Stack 
Next.js

FastAPI

LangChain

ChromaDB

Groq LLM

HuggingFace Embeddings

## Installation


```bash
git clone https://github.com/Abirbenbrahem-Git/doc-ai-assistant.git
cd doc-ai-assistant
```

Navigate to https://console.groq.com
Create API Key
Copy your key

### Backend

**Terminal 1 Backend :**

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` :
GROQ_API_KEY= your_key_here
CHROMA_PERSIST_DIR=./chroma_data
```bash
uvicorn app.main:app --reload --port 8000
```
### Frontend

**Terminal 2 Frontend :**

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```


Open http://localhost:3000
