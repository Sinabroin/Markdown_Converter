# Contributing

Thanks for your interest in File-to-Markdown.

## Getting started

1. Fork the repository and create a feature branch.
2. Use Python 3.12 or newer and create a virtual environment.
3. Install project dependencies from `requirements.txt` for full processing, or install `pytest` and `PyYAML` for dependency-light unit tests.
4. Run `python -m pytest -q` before opening a pull request. Tests needing optional dependencies may be skipped if the packages are not installed.
5. Add tests for behavior changes and describe security implications in your PR.

## Privacy and licensing

- **Never** commit confidential corporate documents, API keys, personal data, or files without redistribution rights.
- Use synthetic fixtures or documents with verified public licenses.
- Preserve the MIT license and third-party notices.
- Treat adding an external API call, model download, or cloud dependency as a security-significant change. Such changes must be opt-in, documented, and covered by tests.

## Scope

Issues and PRs involving scanned-PDF OCR, Korean/English layout handling, table extraction, Markdown quality checks, cross-platform installation, and offline reliability are particularly welcome.
