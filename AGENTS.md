# AGENTS.md

## Build, Lint, Test Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run single test file
pytest tests/test_memory.py

# Run single test function
pytest tests/test_memory.py::test_atom_creation

# Run with coverage
pytest --cov=.

# Lint code
flake8 .

# Type check
mypy .

# Format code
black .

# Sort imports
isort .

# Run all checks (lint + type check + format check)
pre-commit run --all-files
```

## Code Style Guidelines

### Language & Framework
- **Primary Language**: Python 3.10+
- **Async Framework**: Use `asyncio` for I/O-bound operations
- **LLM Framework**: LangChain / LangGraph for LLM integration
- **Task Queue**: Celery for distributed task execution
- **Database**: Neo4j (graph database with vector search)
- **Data Validation**: Pydantic for schema validation

### Imports
- Absolute imports for project modules: `from nakari.memory import MemoryModule`
- Relative imports only within same package: `from .atom_manager import AtomManager`
- Order: stdlib, third-party, local (blank lines between groups)
- Use `isort` to auto-sort

### Formatting
- `black` (88 char width), `flake8`/`ruff` for linting, `mypy` for strict types

### Type Annotations
- **Required**: All functions must have type hints
- Use `Optional[T]` not `T | None` (Python < 3.10 compat)
- `List[T]`, `Dict[K,V]` for collections; `TypedDict`/`dataclass`/`BaseModel` for structured data

### Naming Conventions
- Classes: `PascalCase` (e.g., `MemoryModule`)
- Functions: `snake_case` (e.g., `create_atom`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_TOKENS`)
- Private: `_snake_case`, Modules: `snake_case.py`

### Error Handling
- **Never bare `except:`** - always specify exception type
- Log errors with `logger.error()` and context
- Use `try-except-finally` for cleanup, propagate exceptions up

### Async/Await
- `async def` for I/O-bound ops, use `asyncio.gather()` for parallel calls
- Always use `async with` for context managers

### Database (Neo4j)
- Use prepared statements with parameterized queries
- Implement connection pooling for performance
- Handle Neo4j specific exceptions (TransientError for retry)
- Use transactions for multi-operation writes

### LLM Integration
- **NEVER suppress type errors** with `any`, `@ts-ignore`, `@ts-expect-error`
- Validate outputs with Pydantic, implement retry with exponential backoff
- Use structured prompts (avoid concatenation), cache pure function responses only

### Documentation
- Write docstrings for all public functions/classes (Google or NumPy style)
- Use type hints in docstrings: `param:`, `returns:`, `raises:`
- Document complex algorithms with inline comments, keep READMEs updated

### Architecture & Testing
- Follow module structure from READMEs, separate business logic from LLM
- Use Translation Middleware (Atomizer/Synthesizer) for LLM ↔ graph conversions
- Route async tasks through Tasks module (Celery), never call LLM directly from business logic
- `pytest` for testing, mock external dependencies
- Files: `tests/test_{module_name}.py``

### Git & Security
- Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- Never commit `.env` or secrets, use env vars for config
- Validate external inputs, sanitize LLM outputs, use prepared DB statements
