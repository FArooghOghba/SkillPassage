# SkillPassage

An online marketplace platform enabling Iranian professionals to offer services globally, built with FastAPI.

## 🚀 Features

- Professional service marketplace
- Secure authentication system
- Multi-currency payment processing
- Booking and scheduling system
- Professional verification system
- Analytics dashboard

## 🛠️ Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL with AsyncPG
- **ORM:** SQLAlchemy
- **Migrations:** Alembic
- **Validation:** Pydantic
- **Authentication:** JWT
- **Documentation:** OpenAPI (Swagger)

## 📋 Prerequisites

- Python 3.10+
- Poetry for dependency management
- PostgreSQL

## 🔧 Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/skillpassage.git
cd skillpassage
```

2. Install dependencies with Poetry:
```bash
poetry install
```

3. Set up pre-commit hooks:
```bash
pre-commit install
```

4. Create a `.env` file in the root directory:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/skillpassage
ENVIRONMENT=development
```

5. Run database migrations:
```bash
poetry run alembic upgrade head
```

## 🚀 Running the Application

1. Start the development server:
```bash
poetry run uvicorn skillpassage.main:app --reload
```

2. Access the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 Testing

Run the test suite:
```bash
poetry run pytest
```

## 📁 Project Structure

```
skillpassage/
├── alembic/
├── src/
│   ├── auth/
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── models.py
│   │   ├── dependencies.py
│   │   └── service.py
│   ├── professionals/
│   ├── bookings/
│   ├── payments/
│   ├── config.py
│   ├── database.py
│   └── main.py
├── tests/
├── .env
├── .gitignore
├── pyproject.toml
└── README.md
```

## 🔐 Authentication

The platform uses a multi-level authentication system:
- Basic user authentication
- Professional verification
- Two-factor authentication (optional)
- Session management

## 💳 Payment Processing

Supports multiple payment methods:
- Local Iranian payment gateways
- Cryptocurrency options
- Internal credit system
- Multi-currency support

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 Code Style

This project uses several tools to maintain code quality:
- Flake8 for linting
- isort for import sorting
- mypy for type checking
- pydocstyle for docstring checking
- pre-commit hooks for automated checks

## 📄 License

[Add your license here]

## 👥 Authors

- **Faroogh Oghba** - *Initial work* - [FArooghOghba](https://github.com/FArooghOghba)

## 🙏 Acknowledgments

- FastAPI best practices guide
- Iranian developer community
- [Add other acknowledgments]
