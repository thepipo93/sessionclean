# Contributing to SessionClean

Thank you for your interest in contributing to SessionClean! 🎉

## Getting Started

1. **Fork** the repository
2. **Clone** your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/sessionclean.git
   cd sessionclean
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
4. **Install dev dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

## Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Run tests:
   ```bash
   pytest tests/ -v
   ```
4. Run the linter:
   ```bash
   ruff check src/
   ```
5. Commit and push:
   ```bash
   git commit -m "Add your feature description"
   git push origin feature/your-feature-name
   ```
6. Open a Pull Request

## Code Style

- We use **ruff** for linting
- Line length: 100 characters
- Type hints are encouraged
- Docstrings for all public methods (Google style)

## Testing

- Tests live in the `tests/` directory
- Use **pytest** as the test runner
- Name test files `test_*.py`
- Aim for meaningful tests, not just coverage numbers

## Reporting Bugs

Please open an issue with:
- A clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Your Windows version and Python version

## Feature Requests

Open an issue with:
- A clear description of the feature
- Why it would be useful
- Any implementation ideas you have

## License

By contributing, you agree that your contributions will be licensed under the GPL v3 License.
