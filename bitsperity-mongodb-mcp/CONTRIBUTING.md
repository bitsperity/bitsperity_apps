# Contributing to MongoDB MCP Server

Thank you for your interest in contributing to the MongoDB MCP Server! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues

- **Search first**: Check if your issue already exists in [GitHub Issues](https://github.com/yourusername/mongodb-mcp-server/issues)
- **Be specific**: Include OS, Python version, Docker version, and error messages
- **Minimal reproduction**: Provide the smallest example that demonstrates the issue
- **Use templates**: We provide issue templates to guide you

### Feature Requests

- **Check roadmap**: Review our [project roadmap](https://github.com/yourusername/mongodb-mcp-server/projects) first
- **Discuss first**: Open a discussion before implementing large features
- **Clear use case**: Explain why the feature would be valuable to users

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Follow our conventions** (see below)
4. **Write tests** for new functionality
5. **Update documentation** if needed
6. **Commit with clear messages**
7. **Open a pull request**

## 🏗️ Development Setup

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git

### Setup

```bash
# Fork and clone
git clone https://github.com/yourusername/mongodb-mcp-server.git
cd mongodb-mcp-server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r src/requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Run tests
python -m pytest tests/

# Start development server
python src/simple_mcp_server.py
```

## 📝 Code Style

### Python

- **Follow PEP 8**: Use `black` for formatting
- **Type hints**: Add type annotations for all functions
- **Docstrings**: Use Google-style docstrings
- **Imports**: Sort with `isort`

```python
def establish_connection(connection_string: str) -> Dict[str, Any]:
    """Establish a connection to MongoDB.
    
    Args:
        connection_string: MongoDB connection URI.
        
    Returns:
        Connection result with session_id and server_info.
        
    Raises:
        ConnectionError: If connection fails.
    """
    pass
```

### Git Commits

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
feat: add aggregation pipeline support
fix: resolve connection timeout issue
docs: update installation instructions
test: add integration tests for schema analysis
refactor: simplify connection manager code
```

### Docker

- **Multi-stage builds**: Use efficient Dockerfile patterns
- **Security**: Don't include secrets or sensitive data
- **Minimal images**: Use Alpine or slim base images

## 🧪 Testing

### Running Tests

```bash
# Unit tests
python -m pytest tests/unit/

# Integration tests (requires MongoDB)
docker-compose up -d mongodb
python -m pytest tests/integration/

# All tests
python -m pytest tests/

# With coverage
python -m pytest --cov=src tests/
```

### Writing Tests

- **Test files**: Place in `tests/` directory
- **Naming**: Use `test_*.py` or `*_test.py`
- **Structure**: Mirror the `src/` directory structure
- **Fixtures**: Use pytest fixtures for common setup

```python
import pytest
from src.connection_manager import ConnectionManager

@pytest.fixture
def connection_manager():
    return ConnectionManager(session_ttl=3600)

def test_establish_connection_success(connection_manager):
    # Test implementation
    pass
```

## 📚 Documentation

### Code Documentation

- **Docstrings**: All public functions and classes
- **Type hints**: Use throughout the codebase
- **Comments**: Explain complex logic, not obvious code

### README Updates

- **Keep current**: Update examples when API changes
- **Test examples**: Ensure all code examples work
- **Clear instructions**: Write for beginners

### API Documentation

- **OpenAPI**: Update specs when adding endpoints
- **Examples**: Provide real-world usage examples
- **Error codes**: Document all possible error responses

## 🐛 Debugging

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.debug("Detailed debugging information")
    logger.info("General information")
    logger.warning("Something unexpected happened")
    logger.error("An error occurred")
```

### Environment Variables

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Increase timeouts for debugging
export SESSION_TTL=7200
export CONNECTION_TIMEOUT=600
```

## 🔧 Tools

### Required Development Tools

```bash
# Code formatting
pip install black isort

# Linting
pip install pylint flake8

# Type checking
pip install mypy

# Testing
pip install pytest pytest-cov pytest-mock

# Pre-commit hooks
pip install pre-commit
pre-commit install
```

### VS Code Setup

Recommended extensions:
- Python
- Pylance
- Docker
- GitLens
- Auto Docstring

Settings:
```json
{
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.testing.pytestEnabled": true
}
```

## 🚀 Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in relevant files
- [ ] Git tag created
- [ ] Docker images built and pushed
- [ ] GitHub release created

## 🎯 Roadmap

### Current Priorities

1. **Enhanced MongoDB Support**
   - GridFS file operations
   - Change streams support
   - Transactions

2. **Additional Database Support**
   - PostgreSQL MCP server
   - MySQL MCP server
   - Redis MCP server

3. **Developer Experience**
   - Better error messages
   - Performance monitoring
   - IDE plugins

### Future Ideas

- **GUI Interface**: Web-based database explorer
- **Schema Migration**: Tools for database migrations
- **Performance Analytics**: Query performance insights
- **Multi-tenant Support**: Isolated environments

## 📞 Getting Help

- **Discussions**: Use [GitHub Discussions](https://github.com/yourusername/mongodb-mcp-server/discussions) for questions
- **Discord**: Join our community server (link in README)
- **Issues**: Use for bugs and specific problems
- **Email**: For security issues, contact security@yourproject.com

## 📜 Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it to understand what behavior is expected.

## 🙏 Recognition

Contributors will be:
- Listed in our [CONTRIBUTORS.md](CONTRIBUTORS.md) file
- Mentioned in release notes
- Given repository collaborator status (for significant contributions)

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the MIT License. 