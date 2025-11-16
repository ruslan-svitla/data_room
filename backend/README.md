# Backend Service

This directory contains the backend API for the Data Room application, built with FastAPI.

## Project Structure

The application follows a layered architecture:

- **`app/`**: Main application package
  - **`api/`**: API route handlers (endpoints)
  - **`core/`**: Core configuration, security, and settings
  - **`db/`**: Database connection and session management
  - **`models/`**: SQLAlchemy database models
  - **`schemas/`**: Pydantic schemas for request/response validation
  - **`services/`**: Business logic layer
  - **`utils/`**: Utility functions
- **`tests/`**: Test suite (pytest)
- **`lambda_handler.py`**: Entry point for AWS Lambda deployment

## Getting Started

### Prerequisites

- Python 3.12+
- `uv` (recommended for dependency management) or `pip`

### Setup

1. **Environment Setup**:
   The project uses `uv` for fast dependency management. The included `Makefile` simplifies common tasks.

   ```bash
   # Create virtual environment and install dependencies
   make setup
   make install
   ```

2. **Environment Variables**:
   Copy the example environment file and configure it:

   ```bash
   cp .env.example .env
   ```

3. **Database Initialization**:
   Initialize the database and apply migrations:

   ```bash
   make migrate-up
   make init-db
   ```

## Development

### Running the Server

Start the development server with auto-reload:

```bash
make dev
```
The API will be available at `http://localhost:8000`.

### Testing

Run the test suite:

```bash
make test
```

### Code Quality

Format and lint the code:

```bash
make format
make lint
```

## Database Management

- **Create Migration**: `make migrate m="message"`
- **Apply Migrations**: `make migrate-up`
- **Rollback**: `make migrate-down`
- **Seed Data**: `make init-db-data`

## Deployment

The application is designed to be deployed as an AWS Lambda function using the `lambda_handler.py` entry point. See the `infra/aws` directory for deployment scripts.
