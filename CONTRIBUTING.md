# Contributing to UK Fuel Finder

Thank you for your interest in contributing to the UK Fuel Finder Home Assistant integration!

## Reporting Issues

- Use the [GitHub issue tracker](https://github.com/mretallack/ukfuelfinder-ha/issues)
- Search existing issues before creating a new one
- Include Home Assistant version, integration version, and logs
- Describe steps to reproduce the issue

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ukfuelfinder-ha.git
   cd ukfuelfinder-ha
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Code Standards

- Follow Home Assistant coding standards
- Use type hints
- Add docstrings to all functions and classes
- Keep line length to 100 characters
- Run code formatters before committing:
  ```bash
  black custom_components tests
  isort custom_components tests
  ```

## Testing

- Add tests for new functionality
- Ensure all tests pass:
  ```bash
  pytest
  ```
- Aim for >80% code coverage

## Pull Request Process

1. Update documentation if needed
2. Add your changes to CHANGELOG.md
3. Ensure all tests pass
4. Create a pull request with a clear description
5. Link any related issues

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow

## Questions?

Open an issue for questions or discussion.
