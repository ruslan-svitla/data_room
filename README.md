# Data Room

A secure document management and sharing platform with integration capabilities for Google Drive and other storage providers.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Design Decisions](#design-decisions)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Setup Instructions](#setup-instructions)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Database Configuration](#database-configuration)
  - [Google Drive Integration Setup](#google-drive-integration-setup)
  - [Docker Setup](#docker-setup)
- [Development Workflow](#development-workflow)
- [API Documentation](#api-documentation)
- [Improvement Roadmap](#improvement-roadmap)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Overview

The Data Room application provides a secure platform for storing, managing, and sharing sensitive documents. It includes integration with Google Drive and implements robust authentication and authorization mechanisms to ensure data security.

## Features

- **Document Management**: Upload, organize, and manage documents in a structured folder system
- **User Authentication**: Secure login, registration, and token-based authentication
- **Role-Based Access Control**: Fine-grained permissions for document access
- **Google Drive Integration**: Import documents from connected Google Drive accounts
- **Document Preview**: View documents directly within the application
- **Version Control**: Track document updates and changes
- **Search Functionality**: Quickly find documents based on metadata
- **Responsive Design**: Access from both desktop and mobile devices

## Design Decisions

### Technology Stack

- **Backend**: FastAPI was chosen for its asynchronous capabilities, performance, and automatic OpenAPI documentation generation
- **Frontend**: React with TypeScript provides type safety and component-based architecture for maintainable UI development
- **Database**: SQLAlchemy ORM with SQLite default (configurable for production databases)
- **Authentication**: JWT-based authentication with refresh token mechanism for security and usability
- **File Storage**: Local file system with abstracted storage interface for future cloud storage implementation
- **API Design**: RESTful API with consistent naming conventions and comprehensive validation

### Architecture

- **Layered Backend Architecture**:
  - API layer for request handling
  - Service layer for business logic
  - Repository layer for data access
  - Models for data representation

- **Component-Based Frontend**:
  - Reusable UI components
  - Redux for state management
  - Custom hooks for API interaction
  - Styled components for consistent theming

### Data Model Design

- **User-centric permission model** for secure document access
- **Hierarchical folder structure** to organize documents naturally
- **Flexible metadata schema** for document categorization
- **Separate authentication and data models** for clean separation of concerns

### Integration Approach

- **OAuth2 for Google Drive** - Secure token-based access without storing credentials
- **Abstracted storage interface** - Consistent API regardless of storage provider
- **Metadata synchronization** - Ensures consistency between external sources and local representation

### Security Considerations

- **JWT with short expiration** and refresh token rotation
- **Input validation** at API boundaries
- **Content security policies** to prevent XSS attacks
- **CORS configuration** to control domain access
- **Encrypted storage** for sensitive tokens and user credentials

## Technology Stack

### Backend
- FastAPI (Python)
- SQLAlchemy ORM
- Pydantic for data validation
- Alembic for database migrations
- uvicorn as ASGI server
- JWT for authentication

### Frontend
- React
- TypeScript
- Redux for state management
- Axios for API requests
- Material-UI components
- React Router for navigation

### Development & Deployment
- Docker & Docker Compose
- GitHub Actions for CI/CD
- pytest for backend testing
- Jest & React Testing Library for frontend testing

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 16+
- npm or yarn
- Docker & Docker Compose (optional)
- Google Developer Console account (for Google Drive integration)

### Backend Setup

1. **Clone the repository:**
   ```bash
   git clone git@github.com:ruslan-svitla/data_room.git
   cd data_room
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file with your configuration.

5. **Initialize the database:**
   ```bash
   python -m app.initial_data
   ```

6. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

7. **Start the backend server:**
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be available at http://localhost:8000

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install  # or: yarn install
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   Configure the backend API URL and other settings.

3. **Start the development server:**
   ```bash
   npm start  # or: yarn start
   ```
   The frontend will be available at http://localhost:3000

### Database Configuration

The application uses DynamoDB for database operations. You can work with DynamoDB either in AWS or locally for development.

#### Using DynamoDB Locally

1. **Set up a local DynamoDB instance**:

   Option 1: Using DynamoDB Local:
   ```bash
   # Download and run DynamoDB Local
   mkdir -p ~/dynamodb-local
   cd ~/dynamodb-local
   curl -O https://d18zp2ou2cdphe.cloudfront.net/dynamodb_local_latest.tar.gz
   tar -xzf dynamodb_local_latest.tar.gz
   java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb -port 8000
   ```

   Option 2: Using LocalStack with Docker:
   ```bash
   docker run --name localstack -p 4566:4566 -e SERVICES=dynamodb -d localstack/localstack
   ```

2. **Update your `.env` file** with AWS connection settings:
   ```
   # For DynamoDB Local
   AWS_REGION=us-east-1
   AWS_ACCESS_KEY_ID=dummy
   AWS_SECRET_ACCESS_KEY=dummy
   AWS_ENDPOINT_URL=http://localhost:8000

   # For LocalStack
   # AWS_ENDPOINT_URL=http://localhost:4566
   ```

3. **Create the required DynamoDB tables**:
   ```bash
   cd backend
   python scripts/create_local_dynamodb_tables.py
   ```

4. **Check your DynamoDB connection**:
   ```bash
   python scripts/check_dynamodb_connection.py
   ```

For more detailed information, refer to the [Local DynamoDB Guide](backend/docs/local_dynamodb.md).

### Google Drive Integration Setup

1. **Create a project in Google Cloud Console:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Drive API

2. **Create OAuth credentials:**
   - In the Cloud Console, navigate to "APIs & Services" > "Credentials"
   - Create OAuth 2.0 Client ID (Web application)
   - Add authorized redirect URIs:
     - For development: `http://localhost:8000/api/v1/integrations/google/callback`
     - For production: Add your production callback URL

3. **Configure the application:**
   - Update your `.env` file with the OAuth credentials:
   ```
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_client_secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/integrations/google/callback
   ```

### Docker Setup

The application includes Docker configuration for easy deployment:

1. **Build and start the containers:**
   ```bash
   docker-compose up -d
   ```

2. **Initialize the database:**
   ```bash
   docker-compose exec backend python -m app.initial_data
   ```

3. **Run migrations:**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### AWS Deployment

The application includes a comprehensive set of scripts for deploying to AWS using CloudFormation.

1. **Deploy Infrastructure**:
   ```bash
   cd infra/aws
   ./deploy.sh --type all --stage dev
   ```

2. **Verify Deployment**:
   ```bash
   cd infra/aws
   ./test_deploy.sh --type all --stage dev
   ```

3. **Teardown Infrastructure**:
   ```bash
   cd infra/aws
   ./teardown.sh --type all --stage dev
   ```

For detailed instructions and configuration options, please refer to the [AWS Infrastructure Documentation](infra/aws/README.md).

## Development Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes and commit:**
   ```bash
   git add .
   git commit -m "Add your meaningful commit message"
   ```

3. **Run tests:**
   ```bash
   # Backend
   cd backend
   pytest

   # Frontend
   cd frontend
   npm test
   ```

4. **Push your changes and create a pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

## API Documentation

FastAPI provides automatic API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

- **Backend**: pytest for unit and integration tests
- **Frontend**: Jest and React Testing Library
