Goal: Lay the groundwork for the backend structure, environment, and core services.

Tasks:

Create GitHub repo: skillsync-backend

Initialize a FastAPI project (or Flask/Django if preferred)

Setup folder structure:

skillsync-backend/
├── app/
│   ├── main.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── database/
│   └── utils/
├── requirements.txt
├── .env (for secrets)
├── README.md


Integrate SQLAlchemy + PostgreSQL
Implement authentication with JWT tokens

Create initial API routes for:

/auth/register

/auth/login

/healthcheck

Setup .env handling with python-dotenv

Test with Postman or FastAPI Swagger UI
