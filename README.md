# Warehouse API

A FastAPI-based warehouse management system API.

## Features

- Product management (create, read, update, delete)
- Order management with status tracking
- Stock control
- RESTful API endpoints

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd warehouse_api
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

Start the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Swagger UI documentation: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`

## Project Structure

```
warehouse_api/
├── app/
│   ├── crud/         # Database operations
│   ├── models/       # SQLAlchemy models
│   ├── routers/      # API endpoints
│   ├── schemas/      # Pydantic models
│   ├── utils/        # Utility functions
│   ├── database.py   # Database configuration
│   └── main.py       # Application entry point
├── tests/            # Test files
└── requirements.txt  # Project dependencies
```

## Testing

Run tests with:
```bash
pytest
```

## License

[Add your license here]
