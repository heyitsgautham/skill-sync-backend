# SkillSync Backend

An intelligent internship matching platform that connects students with companies using AI-powered recommendations. The system uses RAG (Retrieval-Augmented Generation) with LLM to analyze student resumes and internship postings for optimal matching.

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT-based auth with bcrypt password hashing
- **Python Version**: 3.9+

## Project Structure

```
skillsync-backend/
├── app/
│   ├── main.py              # Application entry point
│   ├── models/              # Database models
│   │   └── user.py
│   ├── routes/              # API endpoints
│   │   ├── auth.py
│   │   └── health.py
│   ├── services/            # Business logic
│   │   └── auth_service.py
│   ├── database/            # Database configuration
│   │   └── connection.py
│   └── utils/               # Utility functions
│       └── security.py
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (DO NOT COMMIT)
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.9 or higher
- PostgreSQL 12+ (tested with PostgreSQL 14)
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone git@github.com:heyitsgautham/skill-sync-backend.git
   cd skill-sync-backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   The `.env` file is already configured. Update if needed:
   ```env
   DATABASE_URL=postgresql://yourusername@localhost:5432/skillsync
   SECRET_KEY=your-secret-key-here-generate-with-openssl-rand-hex-32
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   PORT=8000
   ```
   
   **Generate a secure SECRET_KEY:**
   ```bash
   openssl rand -hex 32
   ```

5. **Set up PostgreSQL database**
   
   **macOS (using Homebrew):**
   ```bash
   # Install PostgreSQL if not already installed
   brew install postgresql@14
   
   # Start PostgreSQL service
   brew services start postgresql@14
   
   # Create database
   createdb skillsync
   ```
   
   **Linux:**
   ```bash
   sudo systemctl start postgresql
   sudo -u postgres createdb skillsync
   ```
   
   **Windows:**
   ```bash
   # After installing PostgreSQL, use psql:
   psql -U postgres
   CREATE DATABASE skillsync;
   \q
   ```

6. **Run the application**
   ```bash
   python -m app.main
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

The API will be available at `http://localhost:8000`

### Verify Installation

Run the test script to verify all endpoints:
```bash
chmod +x scripts/test_api.sh
./scripts/test_api.sh
```

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## Available Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and receive JWT token

### Health Check
- `GET /api/healthcheck` - Check API and database status

## Testing with Postman/cURL

### Register a new user:
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "securepassword123",
    "full_name": "John Doe",
    "role": "student"
  }'
```

### Login:
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "securepassword123"
  }'
```

### Health Check:
```bash
curl http://localhost:8000/api/healthcheck
```

## User Roles

- **student**: Students can create profiles, upload resumes, and apply for internships
- **company**: Companies can post internships and view matched candidates
- **admin**: Administrators can manage users and access analytics

## Security Features

- JWT-based authentication
- Bcrypt password hashing
- Role-based access control (RBAC) ready
- Input validation with Pydantic
- Environment variable protection

## Development

### Development Workflow

This project follows a PR-based workflow:

1. **Create a feature branch**
   ```bash
   git checkout main
   git pull upstream main
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes and commit**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

3. **Push to remote**
   ```bash
   git push upstream feature/your-feature-name
   ```

4. **Create a Pull Request**
   - Go to GitHub and create a PR from your feature branch to `main`
   - Add description and request review
   - After approval, merge to main

### Running in development mode:
```bash
uvicorn app.main:app --reload --port 8000
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for functions and classes
- Keep functions focused and modular

## Next Steps

- [ ] Implement student profile management
- [ ] Add company profile and internship posting endpoints
- [ ] Integrate RAG system for AI matching
- [ ] Add admin dashboard endpoints
- [ ] Implement file upload for resumes
- [ ] Add rate limiting and advanced security
- [ ] Write comprehensive tests

## Contributing

1. Create a feature branch
2. Make your changes
3. Write/update tests
4. Submit a pull request

## License

[Your License Here]

## Support

For questions or issues, please contact [your-contact-info]
