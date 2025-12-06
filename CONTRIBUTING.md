# Contributing to Fastuner

Thank you for your interest in contributing to Fastuner!

## Development Setup

### Prerequisites

- Python 3.11 or higher
- AWS Account with SageMaker access
- Git

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/0xjav/Fastuner.git
   cd Fastuner
   ```

2. **Create a virtual environment**

   **On macOS/Linux:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   **On Windows:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements-dev.txt
   pip install -e .
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up the database**
   ```bash
   # SQLite auto-creates the database file - just run migrations
   alembic upgrade head
   ```

6. **Run tests**
   ```bash
   pytest tests/ -v
   ```

## Development Workflow

### Code Style

We use the following tools to ensure code quality:

```bash
# Format code
black fastuner/ tests/
isort fastuner/ tests/

# Lint code
ruff check fastuner/ tests/

# Type checking
mypy fastuner/
```

### Running the API Server Locally

```bash
# Development mode with auto-reload
uvicorn fastuner.api.main:app --reload --port 8000

# Visit http://localhost:8000/docs for API documentation
```

### Running the CLI Locally

```bash
# After pip install -e .
fastuner --help

# Or directly
python -m fastuner.cli.main --help
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Testing

### Unit Tests

```bash
pytest tests/unit/ -v
```

### Integration Tests

```bash
# Requires AWS credentials and moto
pytest tests/integration/ -v
```

### Coverage Report

```bash
pytest --cov=fastuner --cov-report=html
open htmlcov/index.html
```

## Project Structure

```
fastuner/
├── api/              # FastAPI endpoints
│   ├── v0/          # V0 API routes
│   └── middleware/  # Auth, error handling
├── core/            # Business logic
│   ├── dataset/     # Dataset validation & splitting
│   ├── training/    # Fine-tune orchestration
│   ├── inference/   # Deployment & inference
│   └── ephemerality/# TTL cleanup
├── models/          # SQLAlchemy models
├── schemas/         # Pydantic schemas
├── cli/             # CLI commands
└── utils/           # AWS clients, helpers
```

## Submitting Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clear, documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests and linting**
   ```bash
   black fastuner/ tests/
   ruff check fastuner/ tests/
   pytest tests/ -v
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push to GitHub**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Provide a clear description of changes
   - Reference any related issues
   - Ensure all CI checks pass

## Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

## Code Review Process

1. All PRs require at least one approval
2. CI/CD checks must pass
3. Code coverage should not decrease
4. Documentation must be updated

## Questions?

Open an issue or reach out to the maintainers!
