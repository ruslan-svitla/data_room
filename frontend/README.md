# Frontend Service

This directory contains the frontend application for the Data Room project, built with React and Vite.

## Project Structure

- **`src/`**: Main application source code
  - **`components/`**: Reusable UI components
  - **`context/`**: React Context definitions
  - **`hooks/`**: Custom React hooks
  - **`pages/`**: Application pages/routes
  - **`services/`**: API integration services
  - **`types/`**: TypeScript type definitions
  - **`test/`**: Test utilities and setup
- **`public/`**: Static assets

## Getting Started

### Prerequisites

- Node.js 18+
- npm

### Setup

1. **Install Dependencies**:

   ```bash
   npm install
   ```

2. **Environment Variables**:
   Copy the example environment file and configure it:

   ```bash
   cp .env.example .env
   ```

## Development

### Running the Server

Start the development server with hot module replacement:

```bash
npm run dev
```

The application will be available at `http://localhost:5173` (default Vite port).

### Building

Build the application for production:

```bash
npm run build
```

### Preview

Preview the production build locally:

```bash
npm run serve
```

### Testing

Run the test suite:

```bash
npm run test
```

## Tech Stack

- **Framework**: React + Vite
- **UI Library**: Material UI (MUI)
- **State Management**: React Query
- **Routing**: React Router DOM
- **HTTP Client**: Axios
