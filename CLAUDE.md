# TAMU Grade Distribution & Course Assistant

## Project Overview

This project is a comprehensive web application for Texas A&M University students to explore grade distribution data and receive intelligent course recommendations through a RAG (Retrieval-Augmented Generation) powered assistant. The system consists of three main components:

1. **Frontend**: React-based web interface with data visualizations and course assistant chat
2. **Backend**: FastAPI server providing grade distribution APIs and RAG-powered course advisory
3. **RAG Scraper**: Data collection and embedding system for course information

## Architecture

```
Frontend (React/Vite) → Backend (FastAPI) → Databases:
                                         ├── MySQL (RDS) - Grade data
                                         └── PostgreSQL/pgvector (Neon) - RAG embeddings
```

## Components

### Frontend (`grade-distribution-frontend/`)
- **Framework**: React 18 with Vite build system
- **Styling**: Inline CSS with dark theme
- **Charts**: Recharts library for data visualization
- **Key Components**:
  - `GpaTime.jsx`: Course GPA trends over time
  - `Insights.jsx`: Department-level analytics dashboards  
  - `CourseAssistant.jsx`: RAG-powered chat interface
  - Various chart components for data visualization

#### API Connections
- Uses environment variables for backend URL configuration:
  - `VITE_API_BASE_URL` for RAG endpoints (defaults to 'https://tamu-gpa-dist.onrender.com')
  - `VITE_BACKEND_URL` for grade data endpoints (defaults to 'http://127.0.0.1:8000')
- Vite proxy configured for local development (`/api` routes → `http://127.0.0.1:8000`)

### Backend (`backend/`)
- **Framework**: FastAPI with CORS middleware
- **Databases**: 
  - MySQL (RDS) for structured grade data
  - PostgreSQL with pgvector (Neon) for RAG embeddings
- **AI Integration**: OpenAI API for embeddings and chat completions
- **Key Features**:
  - Grade distribution analytics endpoints
  - RAG search and advisory endpoints
  - Health check functionality
  - Dual database architecture

#### Main Endpoints
- `GET /health` - Database connectivity check
- `GET /grades/trends` - Course GPA trends over time
- `GET /insights/*` - Various analytics endpoints
- `GET /courses` - Course name autocomplete
- `POST /rag/search` - Semantic search over course data
- `POST /rag/advise` - AI-powered course recommendations

### RAG System (`rag_scraper/`)
- **Data Sources**: 
  - TAMU course catalog scraping
  - Grade distribution PDF processing
  - Structured grade data aggregation
- **Pipeline**:
  1. `scraper.py`: Web scraping of course descriptions from catalog.tamu.edu
  2. `converter.py`: Data transformation and aggregation
  3. `load_to_neon.py`: Embedding generation and database loading
- **Output**: JSONL files with course data, grade statistics, and metadata

## Data Flow

1. **Data Collection**: RAG scraper harvests course descriptions and grade data
2. **Embedding Generation**: OpenAI embeddings created for semantic search
3. **Database Storage**: 
   - Structured grade data → MySQL
   - Embeddings and metadata → PostgreSQL/pgvector
4. **Frontend Requests**: React app queries both databases via FastAPI
5. **RAG Advisory**: User questions trigger semantic search + GPT-4 response generation

## Environment Variables

### Backend
- `RDS_DATABASE_URL`: MySQL connection string
- `VEC_DATABASE_URL`: PostgreSQL connection string  
- `OPENAI_API_KEY`: OpenAI API key
- `EMBED_MODEL`: Embedding model (default: text-embedding-3-small)
- `CHAT_MODEL`: Chat model (default: gpt-4o-mini)

### Frontend
- `VITE_API_BASE_URL`: Backend URL for RAG endpoints
- `VITE_BACKEND_URL`: Backend URL for grade data endpoints

## Development Commands

### Frontend
```bash
cd grade-distribution-frontend
npm install
npm run dev       # Development server
npm run build     # Production build
npm run lint      # Code linting
```

### Backend
```bash
cd backend
pip install -r requirements.txt
python application.py  # Run FastAPI server
```

### RAG Data Pipeline
```bash
cd rag_scraper
python scraper.py     # Scrape course catalog
python converter.py   # Process and aggregate data
python load_to_neon.py # Generate embeddings and load to database
```

## Known Issues & Connection Points

### Frontend-Backend Integration
- **Environment Variable Inconsistency**: Frontend uses different env var names for the same backend
  - `CourseAssistant.jsx` uses `VITE_API_BASE_URL` 
  - `GpaTime.jsx` uses `VITE_BACKEND_URL`
  - Both should point to the same FastAPI server but with different defaults

### API Configuration
- Production deployment uses Render.com: `https://tamu-gpa-dist.onrender.com`
- Local development expects backend on `http://127.0.0.1:8000`
- Vite proxy handles `/api` prefixed requests in development

### Database Dependencies
- Requires both MySQL (RDS) and PostgreSQL (Neon) to be properly configured
- RAG functionality depends on OpenAI API availability
- Health check endpoint verifies all database connections

## Testing & Quality
- Frontend uses ESLint for code quality
- Backend includes comprehensive error handling
- RAG scraper has retry logic and rate limiting
- Health check endpoint monitors system status