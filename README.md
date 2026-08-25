# 🤖 AI Software Engineering Copilot

> An AI-powered developer assistant that understands GitHub repositories using Retrieval-Augmented Generation (RAG), vector search, and LLMs to help developers analyze, understand, and work with unfamiliar codebases.

🌐 **Live Application:** https://ai-software-engineering-copilot.vercel.app  
⚙️ **Backend API:** https://ai-software-engineering-copilot.onrender.com

---

## 📌 Project Context

Modern software projects can contain hundreds or even thousands of files. Understanding an unfamiliar codebase often requires developers to manually search through files, trace dependencies, understand architecture, identify bugs, review security issues, write tests, and maintain documentation.

This process can be time-consuming, especially when joining an existing project or working with a large repository.

**AI Software Engineering Copilot** was built to solve this problem.

The platform allows developers to connect a GitHub repository and interact with it using natural language. Instead of sending the entire repository directly to an LLM, the system uses a **Retrieval-Augmented Generation (RAG)** pipeline to retrieve only the most relevant parts of the codebase before generating an AI response.

The result is a repository-aware AI assistant capable of understanding the actual codebase and providing developer-focused insights.

---

# 🎯 Problem

Developers working with unfamiliar repositories commonly need to answer questions such as:

- Where is authentication implemented?
- How is the application structured?
- What are the main backend components?
- Where could bugs exist?
- Are there potential security vulnerabilities?
- How can this code be optimized?
- What tests should be written?
- How should this project be documented?
- What does the deployment architecture look like?

Manually answering these questions requires navigating through many files and understanding the relationships between them.

---

# 💡 Solution

AI Software Engineering Copilot provides a single interface for repository-level code intelligence.

A developer can:

```text
Connect GitHub Repository
          ↓
Index Repository
          ↓
Ask Questions / Run AI Analysis
          ↓
Retrieve Relevant Code
          ↓
Generate Context-Aware Response
```

The system uses RAG so that the LLM receives relevant code from the selected repository rather than relying only on its general knowledge.

---

# ✨ Features

## 🔐 Authentication

- User registration
- User login
- Token-based authentication
- Protected API routes
- User-specific repositories
- Repository ownership validation

## 📦 Repository Management

- Connect GitHub repositories
- Support multiple repositories
- Repository metadata management
- Repository deletion
- Repository indexing
- Index status tracking
- Repository-specific AI analysis

# 🧠 AI Features

| Feature | Description |
|---|---|
| 🔍 **Explain** | Understand code, architecture, and implementation |
| 🐛 **Bug Analysis** | Identify potential bugs and problematic code |
| ⚡ **Optimization** | Find performance and code-quality improvements |
| 🔒 **Security Analysis** | Identify potential security issues |
| 🧪 **Test Generation** | Generate relevant test cases |
| 📚 **Documentation** | Generate technical documentation |
| 📐 **UML** | Generate architecture/UML diagrams using Mermaid |
| 🚀 **Deployment** | Analyze deployment requirements and architecture |
| 💬 **Ask** | Ask natural-language questions about the repository |

---

# 🔄 RAG Architecture

Retrieval-Augmented Generation is the core of the application.

Instead of passing an entire repository to the LLM, the system retrieves the most relevant code for each request.

```text
                     GitHub Repository
                            │
                            ▼
                    Repository Files
                            │
                            ▼
                      Code Chunking
                            │
                            ▼
                    Embedding Generation
                            │
                            ▼
                     Qdrant Vector DB
                            │
                            │ User Question
                            ▼
                     Query Embedding
                            │
                            ▼
                  Semantic Vector Search
                            │
                            ▼
                   Relevant Code Chunks
                            │
                            ▼
                    Repository Context
                            │
                            ▼
                         Gemini
                            │
                            ▼
                    AI Generated Result
```

## Why RAG?

A large repository may contain thousands of files. Sending the entire repository to an LLM for every request would be expensive, slow, and difficult to scale.

RAG retrieves only the code relevant to the current request.

### Example

A developer asks:

> How is authentication implemented?

The retrieval layer may find:

```text
backend/app/api/routes/auth.py
backend/app/services/auth.py
backend/app/models/user.py
```

Those relevant chunks are then supplied to the LLM.

---

# 🧩 Repository Isolation

The system supports multiple repositories.

Each vector stored in Qdrant contains repository-specific metadata such as:

```json
{
  "repositoryId": "...",
  "indexVersion": "..."
}
```

Retrieval is filtered using this metadata so that code from different repositories remains logically separated.

---

# 🏗️ System Architecture

```text
                         ┌──────────────────────┐
                         │      Frontend        │
                         │     React + Vite     │
                         │        Vercel        │
                         └──────────┬───────────┘
                                    │
                               REST API
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │       FastAPI        │
                         │       Backend        │
                         │        Render        │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
        ┌───────────┐        ┌───────────┐        ┌───────────┐
        │  MongoDB  │        │   Redis   │        │  Qdrant   │
        │ Users     │        │  Cache    │        │ Embeddings│
        │ Repos     │        │           │        │ Chunks    │
        │ Metadata  │        │           │        │           │
        └───────────┘        └───────────┘        └─────┬─────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │       RAG       │
                                              │    Retrieval    │
                                              └────────┬────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │     Gemini      │
                                              │      LLM        │
                                              └─────────────────┘
```

---

# 🔧 Backend Architecture

The backend is built using **FastAPI** and follows a modular service-oriented structure.

```text
backend/
│
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── repositories.py
│   │       ├── indexing.py
│   │       ├── rag.py
│   │       ├── explanation.py
│   │       ├── bugs.py
│   │       ├── optimization.py
│   │       ├── security.py
│   │       ├── tests.py
│   │       ├── documentation.py
│   │       ├── uml.py
│   │       └── deployment.py
│   │
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   └── services/
│       ├── ai/
│       ├── chunking/
│       ├── embeddings/
│       ├── github/
│       ├── indexing/
│       ├── rag/
│       └── vector/
│
└── tests/
```

---

# 🤖 LLM Provider Architecture

The AI layer uses an abstraction instead of coupling application logic directly to a specific LLM implementation.

```text
                 ┌─────────────────┐
                 │   LLMProvider   │
                 │   Abstraction   │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ GeminiProvider  │
                 └────────┬────────┘
                          │
                          ▼
                    Gemini API
```

The provider supports free-form and structured generation. Structured responses are validated using Pydantic models.

---

# 📊 Structured AI Responses

```text
Prompt
  ↓
Gemini
  ↓
JSON Response
  ↓
Pydantic Validation
  ↓
Typed Result
  ↓
API Response
```

This reduces the risk of malformed AI responses reaching the frontend.

---

# 🗄️ Database Architecture

## MongoDB

Used for:

- Users
- Repositories
- Repository metadata
- Ownership
- Indexing information

## Redis

Used as a caching layer to reduce repeated operations and improve performance.

The backend supports graceful degradation if Redis becomes temporarily unavailable.

## Qdrant

Used as the vector database for semantic code retrieval.

Production configuration:

```text
Vector size: 768
Distance: Cosine
```

Payload metadata includes:

```text
repositoryId
indexVersion
```

---

# 🔐 Security

The backend includes:

- Token-based authentication
- Protected API routes
- Repository ownership validation
- Request validation
- Environment-based secret management
- CORS configuration
- Structured AI output validation
- Secrets excluded from source control

Example environment variables:

```env
LLM_API_KEY=your_gemini_api_key
MONGODB_URI=your_mongodb_connection_string
REDIS_URL=your_redis_connection_url
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
EMBEDDING_API_KEY=your_embedding_api_key
```

> ⚠️ Never commit `.env` files, API keys, database credentials, or Redis tokens to GitHub.

---

# 📡 API

## Authentication

```http
POST /api/auth/register
POST /api/auth/login
```

## Repository Management

```http
GET    /api/repositories
POST   /api/repositories
GET    /api/repositories/{repository_id}
DELETE /api/repositories/{repository_id}
```

## Repository Indexing

```http
POST /api/repositories/{repository_id}/index
GET  /api/repositories/{repository_id}/index-status
```

## AI Features

```http
POST /api/repositories/{repository_id}/explain
POST /api/repositories/{repository_id}/bugs
POST /api/repositories/{repository_id}/optimize
POST /api/repositories/{repository_id}/security
POST /api/repositories/{repository_id}/uml
POST /api/repositories/{repository_id}/tests
POST /api/repositories/{repository_id}/documentation
POST /api/repositories/{repository_id}/deployment
POST /api/repositories/{repository_id}/ask
```

---

# 💬 Example Workflow

```text
1. User logs in
       ↓
2. User connects GitHub repository
       ↓
3. Backend stores repository metadata
       ↓
4. User starts indexing
       ↓
5. GitHub files are processed
       ↓
6. Files are split into chunks
       ↓
7. Embeddings are generated
       ↓
8. Vectors are stored in Qdrant
       ↓
9. User asks a question
       ↓
10. Relevant vectors are retrieved
       ↓
11. Repository context is created
       ↓
12. Gemini receives the context
       ↓
13. Structured response is generated
       ↓
14. Frontend displays the result
```

---

# 💻 Frontend

The frontend is a React/Vite application deployed on Vercel.

**Production frontend:**

https://ai-software-engineering-copilot.vercel.app

The frontend communicates with the FastAPI backend through REST APIs.

---

# 🚀 Deployment

```text
                    Internet
                       │
                       ▼
              ┌─────────────────┐
              │     Vercel      │
              │ React Frontend  │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │     Render      │
              │ FastAPI Backend │
              └───────┬─────────┘
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
   MongoDB          Redis          Qdrant
                                      │
                                      ▼
                                   Gemini
```

### Production URLs

**Frontend:**  
https://ai-software-engineering-copilot.vercel.app

**Backend:**  
https://ai-software-engineering-copilot.onrender.com

---

# ⚙️ Local Development

## Prerequisites

- Python 3.12+
- Node.js
- `uv`
- MongoDB
- Redis
- Qdrant
- Gemini API access

## Backend

```bash
cd backend
uv sync
```

Create:

```text
backend/.env
```

Configure the required environment variables.

Run:

```bash
uv run uvicorn app.main:app --reload --port 8000
```

API:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

## Frontend

```bash
cd frontend
npm install
```

Create:

```text
frontend/.env
```

Set:

```env
VITE_API_URL=http://localhost:8000/api
```

Run:

```bash
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# 🧪 Testing

The backend includes automated tests covering authentication, repository management, indexing, RAG, and AI features.

Run:

```bash
uv run pytest -q
```

Verified result:

```text
41 passed
```

### Ruff

```bash
uv run ruff check app tests
```

### MyPy

```bash
uv run mypy app
```

---

# 🛡️ Reliability

The backend includes:

- Asynchronous FastAPI services
- Request validation
- Error handling
- LLM retry logic
- Configurable model fallback
- Redis graceful degradation
- Repository ownership checks
- Structured AI output validation
- Request logging
- Startup checks for external services

---

# 🌍 Real-World Use Cases

### 👨‍💻 Developer Onboarding

Understand an unfamiliar repository quickly.

### 🐛 Debugging

Find potential bugs in specific parts of a codebase.

### 🔒 Security Review

Identify possible security vulnerabilities.

### 🧪 Test Generation

Generate tests based on actual implementation.

### 📚 Documentation

Generate documentation for unfamiliar components.

### 🏗️ Architecture Understanding

Generate UML/architecture diagrams and explanations.

### 💬 Repository Q&A

Ask natural-language questions about the codebase.

---

# 🎯 Engineering Highlights

This project demonstrates:

- Full-stack development
- REST API architecture
- FastAPI
- React/Vite
- Authentication
- Async Python
- MongoDB
- Redis caching
- Qdrant vector search
- Embeddings
- Retrieval-Augmented Generation
- Gemini LLM integration
- Structured LLM outputs
- Pydantic validation
- GitHub integration
- Multi-repository support
- Automated testing
- Static type checking
- Linting
- Cloud deployment

---

# 📈 Scalability

The architecture separates:

```text
API Layer
     ↓
Business Services
     ↓
AI / RAG Layer
     ↓
Data Layer
```

Potential scaling improvements include:

- Background indexing workers
- Queue-based processing
- Incremental indexing
- Horizontal API scaling
- Distributed caching
- Streaming LLM responses
- Repository-level indexing pipelines
- Monitoring and metrics

---

# 🔮 Future Improvements

- GitHub OAuth
- GitHub webhook-based automatic re-indexing
- Incremental indexing
- Pull request analysis
- AI-generated code fixes
- Streaming LLM responses
- Background indexing workers
- Additional LLM providers
- Repository analytics
- Advanced dependency analysis
- Monitoring and observability

---

# 👨‍💻 Author

**Vedansh Joshi**

GitHub:  
https://github.com/Vedanshjoshi05

---

# ⭐ Project

If you find this project useful, consider giving the repository a ⭐ on GitHub.
