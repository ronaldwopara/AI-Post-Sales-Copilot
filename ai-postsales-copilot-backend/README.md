# A comprehensive FastAPI backend for AI-powered post-sales contract management with NLP capabilities and CRM integrations

## Features

- **Contract Management**: Upload, parse, and manage contracts with AI/NLP extraction
- **CRM Integration**: Sync with Salesforce and HubSpot
- **Dashboard Analytics**: Real-time metrics and insights
- **NLP Processing**: Extract key fields from contracts (renewal dates, payment terms, obligations)
- **Data Pipeline**: Unified customer data from multiple sources

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (SQLite for local development)
- **ORM**: SQLAlchemy
- **NLP**: spaCy, Transformers
- **File Processing**: PyPDF2, python-docx
- **CRM**: Salesforce API, HubSpot API
- **Background Tasks**: Celery + Redis

## Setup Instructions

### 1. Clone the repository

```bash
git clone <repository-url>
cd ai-postsales-copilot
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install spaCy model

```bash
python -m spacy download en_core_web_sm
```

### 5. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 6. Database setup

```bash
# Initialize Alembic
alembic init migrations

# Create first migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 7. Run the application

```bash
# Development
uvicorn app.main:app --reload --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, access the interactive API documentation at:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

## Key Endpoints

### Contracts

- `POST /api/contracts/upload` - Upload and parse contract
- `GET /api/contracts` - List all contracts
- `GET /api/contracts/{id}` - Get contract details
- `PUT /api/contracts/{id}` - Update contract
- `POST /api/contracts/{id}/reparse` - Re-parse contract with NLP

### Dashboard

- `GET /api/dashboard/summary` - Dashboard summary metrics
- `GET /api/dashboard/renewal-forecast` - Contract renewal forecast
- `GET /api/dashboard/metrics` - Detailed business metrics

### CRM

- `POST /api/crm/sync` - Trigger CRM synchronization
- `GET /api/crm/records` - List CRM records
- `GET /api/crm/sync-status` - Get sync status

## Environment Variables

### Required

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key

### Optional (for full functionality)

- `OPENAI_API_KEY`: For advanced NLP features
- `SALESFORCE_CLIENT_ID`: Salesforce OAuth client ID
- `SALESFORCE_CLIENT_SECRET`: Salesforce OAuth client secret
- `HUBSPOT_API_KEY`: HubSpot API key

## Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## Docker Support

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t ai-postsales-copilot .
docker run -p 8000:8000 --env-file .env ai-postsales-copilot
```

## Production Deployment

### Using Gunicorn

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Docker Compose

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db/postsales
    depends_on:
      - db
      - redis

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=postsales
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7

volumes:
  postgres_data:
```

## Background Tasks with Celery

```python
# celery_app.py
from celery import Celery
from app.config import settings

celery_app = Celery(
    'tasks',
    broker=settings.redis_url,
    backend=settings.redis_url
)

# Run worker
celery -A celery_app worker --loglevel=info


## License

MIT License

## Support

For issues and questions, please open an issue in the repository.


## Next Steps

1. **Database Migrations**: Run `alembic init migrations` and create your first migration
2. **Environment Setup**: Copy `.env.example` to `.env` and configure your settings
3. **Install Dependencies**: Run `pip install -r requirements.txt`
4. **Download NLP Models**: Run `python -m spacy download en_core_web_sm`
5. **Run Application**: Start with `uvicorn app.main:app --reload`
6. **Test Endpoints**: Access http://localhost:8000/docs for interactive API testing

The backend is now ready for integration with your frontend application!
