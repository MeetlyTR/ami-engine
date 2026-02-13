# Contributing to AMI-ENGINE

Thank you for your interest in contributing to AMI-ENGINE!

---

## Code of Conduct

- Be respectful and professional
- Focus on constructive feedback
- Respect intellectual property and attribution

---

## How to Contribute

### Reporting Issues

- **Bug Reports**: Use GitHub Issues with clear reproduction steps
- **Security Issues**: See SECURITY.md for private reporting
- **Feature Requests**: Open an issue with clear use case description

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Update documentation if needed
6. Commit with clear messages (`git commit -m 'Add amazing feature'`)
7. Push to your branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Setup

```bash
# Clone repository
git clone https://github.com/MeetlyTR/ami-engine.git
cd ami-engine

# Install in editable mode
pip install -e ".[dev]"

# Run tests
python run_all_tests.py
```

---

## Contribution Guidelines

### Code Style

- Follow PEP 8 (Python style guide)
- Use type hints where applicable
- Keep functions focused and under 100 lines
- Add docstrings for public APIs

### Testing

- All new features should include tests
- Run `python run_all_tests.py` before submitting PR
- Maintain or improve test coverage

### Documentation

- Update README.md for user-facing changes
- Update CHANGELOG.md for notable changes
- Add docstrings for new functions/classes

### Public API Changes

**Breaking changes** to public API require:
- Major version bump (1.0 → 2.0)
- Migration guide in CHANGELOG.md
- Deprecation warnings for at least one minor version

**Public API** (stable):
- `ami_engine.decide()`
- `ami_engine.replay_trace()`
- `ami_engine.moral_decision_engine()`
- `ami_engine.get_config()`, `ami_engine.list_profiles()`
- CLI commands (`ami-engine dashboard`, etc.)

---

## Areas for Contribution

### High Priority

- Additional config profiles for specific domains
- Performance optimizations
- Extended test coverage
- Documentation improvements

### Medium Priority

- Additional visualization plots
- Example adapters for common domains
- CI/CD improvements
- Internationalization (i18n) expansion

### Low Priority

- Additional example scripts
- Documentation translations
- Code style improvements

---

## Questions?

- **General Questions**: Open a GitHub Discussion
- **Security**: See SECURITY.md
- **Contact**: mucahit.muzaffer@gmail.com

---

**Thank you for contributing to AMI-ENGINE!**
