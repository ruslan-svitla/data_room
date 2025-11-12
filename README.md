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
   git clone https://github.com/yourusername/data_room.git
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

The application uses SQLAlchemy ORM, which supports multiple database backends. By default, it's configured to use SQLite for development, but for production, you should consider using a more robust database like PostgreSQL.

#### Using PostgreSQL

1. **Install PostgreSQL** and create a new database:
   ```bash
   # On Ubuntu/Debian
   sudo apt install postgresql
   sudo -u postgres createdb data_room
   sudo -u postgres createuser --interactive
   ```

2. **Update your `.env` file** with PostgreSQL connection string:
   ```
   DATABASE_URL=postgresql+asyncpg://username:password@localhost/data_room
   ```

3. **Install the required Python driver**:
   ```bash
   pip install asyncpg
   ```

4. **Run migrations** with the new database:
   ```bash
   alembic upgrade head
   ```

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

## Improvement Roadmap

### Database Improvements
- **Migration to PostgreSQL**:
  - Replace SQLite with PostgreSQL for better performance and concurrency
  - Implement connection pooling for efficient resource usage
  - Add database replication for high availability
  - Implement proper indexing strategy for optimized queries

### Infrastructure and DevOps
- CI/CD pipeline implementation with GitHub Actions
- Comprehensive branch protection rules
- Infrastructure as Code for consistent deployments
- Enhanced Docker setup with Kubernetes orchestration
- Cloud-native storage with S3 integration

### Security Enhancements
- Centralized credential management with AWS Secrets Manager or HashiCorp Vault
- Multi-factor authentication implementation
- Fine-grained RBAC permissions
- API rate limiting and enhanced protection
- Automated security scanning in the CI pipeline

### Additional Integrations
- Microsoft OneDrive/SharePoint integration
- Dropbox integration
- Box integration
- Custom API integrations for enterprise clients

### Feature Enhancements
- Document OCR processing
- AI-based document classification
- Automated metadata extraction
- Document version control system
- Feature flag system for controlled rollouts
- Enhanced search with full-text capabilities

### Performance Optimizations
- Implement caching strategy (Redis)
- API response optimization
- Frontend bundle size reduction
- Lazy loading for large document collections
- Optimized database query patterns

For a complete list of planned improvements, see the [improvement_roadmap.md](improvement_roadmap.md) file.

## Testing

- **Backend**: pytest for unit and integration tests
- **Frontend**: Jest and React Testing Library
- **API Testing**: Postman collections included in `/docs/postman`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

Please follow our coding standards and include tests for new features.

## License

[MIT License](LICENSE)