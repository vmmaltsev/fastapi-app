# FastAPI PostgreSQL Application

Simple FastAPI application with PostgreSQL connection for managing records.

## Features

- CRUD operations for records
- Web interface with HTML templates
- API endpoints for programmatic access
- Docker and Docker Compose setup
- Testing with pytest

## Setup

### Environment Variables

The application uses environment variables for configuration. Create a `.env` file in the root directory based on the `.env.example` template:

```bash
cp .env.example .env
```

Then edit the `.env` file with your actual configuration:

```
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fastapi_app
ENVIRONMENT=development
```

### Running with Docker Compose

1. Build and start the containers:

```bash
docker-compose up -d
```

2. Access the application at http://localhost:8000

### Running Tests

Run tests using Docker Compose:

```bash
docker-compose run test
```

Or with verbose output:

```bash
docker-compose run test pytest tests/ -v
```

## API Endpoints

- `GET /` - Web interface
- `POST /records/` - Create a record via web form
- `POST /records/{record_id}/delete` - Delete a record via web form
- `GET /api/records/` - List all records (API)
- `POST /api/records/` - Create a record (API)
- `GET /api/records/{record_id}` - Get a specific record (API)
- `PUT /records/{record_id}` - Update a record (API)
- `GET /health` - Health check endpoint

## Security Notes

- Never commit the `.env` file to version control
- Use strong, unique passwords for database credentials
- In production, consider using a secrets management solution
- Regularly update dependencies to patch security vulnerabilities 