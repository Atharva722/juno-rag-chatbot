🚀 Juno — Private Retrieval-Augmented Generation (RAG) Assistant

Juno is a local-first, production-style Retrieval-Augmented Generation (RAG) system that allows users to ask intelligent questions across their own document collections.
It is designed to mirror how real-world enterprise GenAI assistants are built — with persistent storage, metadata-aware retrieval, and a clean API-driven architecture.

Unlike generic chatbots, Juno grounds every response in user-provided documents, enabling accurate, contextual, and explainable answers.

✨ Key Capabilities

Multi-Document Question Answering
Ask questions across multiple uploaded documents simultaneously.

Local & Private by Design
Documents and embeddings are stored locally. Only LLM inference requests are sent to the model provider.

Persistent Knowledge Base
Indexed documents remain available across application restarts.

Metadata-Aware Retrieval
Each document is tracked using unique identifiers for reliable indexing and deletion.

Pluggable Model Architecture
Supports configurable LLM backends with Gemini as the default.

Modern Web Interface
Clean UI built with FastAPI, Tailwind CSS, and vanilla JavaScript.

🧠 System Architecture
User Interface
      ↓
FastAPI Backend
      ↓
RAG Pipeline (LangChain)
      ↓
ChromaDB (Vector Store)
      ↓
Gemini LLM

🛠️ Tech Stack
Backend

Python 3.10+

FastAPI

Uvicorn

RAG & AI

LangChain

Gemini (LLM)

Hugging Face Sentence Transformers (Embeddings)

Storage

ChromaDB — persistent vector storage

SQLite — document metadata & chat logs

Frontend

HTML

Tailwind CSS

JavaScript

📂 Supported Document Formats

.pdf

.docx

.html

.txt

.csv

📌 Core Engineering Decisions

Lazy Loading of RAG Components
RAG pipelines are initialized only when needed, ensuring faster application startup and graceful degradation.

Persistent Vector Storage
ChromaDB is used to ensure embeddings survive restarts and allow document-level deletion.

Session-Aware Conversations
Each chat interaction is associated with a session ID for tracking and future extensibility.

Database-Backed Document Management
Uploaded files are indexed, listed, and deleted using consistent database records.

🚀 Running Juno Locally
1️⃣ Clone the Repository
git clone <YOUR_GITHUB_REPO_URL>
cd juno

2️⃣ Create & Activate Virtual Environment

Windows

python -m venv venv
.\venv\Scripts\Activate.ps1


macOS / Linux

python3 -m venv venv
source venv/bin/activate

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Environment Configuration

Create a .env file in the root directory:

GEMINI_API_KEY=your_gemini_api_key_here
HUGGINGFACEHUB_API_TOKEN=your_huggingface_token_here

5️⃣ Run the Application
uvicorn main:app --reload


The application will be available at:

http://127.0.0.1:8000

🔁 User Flow

Open the landing page.

Navigate to the chat interface.

Upload one or more documents.

Wait for indexing to complete.

Ask questions grounded in your uploaded content.

Optionally delete documents to update the knowledge base.

📁 Project Structure
juno/
├── static/
│   ├── index.html        # Chat UI
│   ├── landing.html      # Landing page
│   └── js/               # Frontend logic
├── uploads/              # Uploaded documents
├── main.py               # FastAPI application
├── langchain_utils.py    # RAG pipeline logic
├── chroma_utils.py       # Vector store operations
├── app_data.db           # SQLite database
├── requirements.txt
├── .env
└── README.md

🚧 Known Limitations

Designed for single-user, local usage

No authentication layer (can be added)

Evaluation metrics for RAG responses not automated (future scope)

🔮 Future Enhancements

Source citation in responses

Advanced chunking & similarity thresholds

Role-based access control

RAG evaluation metrics (faithfulness, relevance)

Cloud deployment support

👨‍💻 Author

Atharva Chalikwar
AI / ML Engineer
📌 GitHub: (add link)
📌 LinkedIn: (add link)

📄 License

MIT License