# FastAPI Starter Template

A modern FastAPI starter template with authentication, database integration, and best practices.

## Features

- FastAPI with modern Python type hints
- SQLAlchemy ORM integration
- JWT Authentication
- PostgreSQL database support
- Alembic migrations
- Environment variable configuration
- Pydantic models for request/response validation

## Setup

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with the following variables:

```
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

4. Initialize the database:

```bash
alembic upgrade head
```

5. Run the application:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the application is running, you can access:

- Swagger UI documentation: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`

## Project Structure

```
app/
├── alembic/           # Database migrations
├── api/              # API routes
├── core/             # Core configurations
├── db/               # Database session and base
├── models/           # SQLAlchemy models
├── schemas/          # Pydantic models
└── main.py          # Application entry point
```
