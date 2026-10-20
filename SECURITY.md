# Security policy

File-to-Markdown is intended to support privacy-conscious document processing. **Do not assume that an installation is fully air-gapped solely because its cloud integrations are disabled.**

## Processing policy

- Cloud processing through the project's OpenAI- and Azure-specific modes is **disabled by default**.
- Explicitly authorized inputs may use `--allow-cloud`; do not use this option with confidential documents unless your organization's policy permits the transfer.
- Basic PDF and Office extraction uses MarkItDown. Local image and scanned-PDF OCR use PaddleOCR (3.x required for scanned PDFs). OCR model weights or Python dependencies may require downloads during installation or first use.
- Optional `--offline` blocks Python-level socket access during processing, but cannot block networking performed by native libraries or spawned processes. Use OS-level or network egress controls for isolation.
- An actual offline / air-gapped deployment additionally requires pre-provisioned dependencies and OCR weights, approved software supply chain, and network egress controls enforced outside this Python application.
- Scanned-PDF page OCR is implemented with a mocked integration test but has not been validated using actual enterprise PDF scans. Do not assume production OCR accuracy.
- Converted Markdown, intermediate files, and JSON logs may contain sensitive information. Store these only on approved devices, control filesystem permissions, and apply suitable retention policies.
- The `input/` directory is ignored for new files; files already committed to Git history remain accessible until separately removed from history.

## Reporting a vulnerability

Please avoid creating a public GitHub issue containing proof-of-concept exploit details, secrets, credentials, or confidential documents. Contact the project maintainer through their GitHub profile to coordinate a private report.

## Supported versions

The repository is early-stage and does not yet provide a formal security-support or patched-release guarantee.
