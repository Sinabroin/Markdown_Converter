# File-to-Markdown

**Local-first document-to-Markdown preprocessing for private AI and RAG workflows.**

A Python pipeline for preparing PDF, Word, Excel, PowerPoint, images, and other document formats as cleaned Markdown. It combines [Microsoft MarkItDown](https://github.com/microsoft/markitdown) for document extraction with [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) for local image OCR, plus format routing, normalization, validation, batch conversion, and JSON logs.

This project grew from a practical constraint: organizations handling confidential information often cannot send their documents to external LLM services. This repository provides local processing paths for preparing documents before they are indexed into an internal retrieval system or used in an authorized model-training pipeline.

**Early-stage project:** there is no claim of independent security certification, enterprise-wide deployment, or complete air-gap support.

## What it does

- Routes files by extension, with MIME detection fallback.
- Extracts common documents through MarkItDown, and image text or scanned-PDF pages through PaddleOCR 3.x (legacy 2.x image OCR is supported).
- Preserves the initial extraction separately from the normalized Markdown.
- Checks output length, repetition, and extraction ratios.
- Converts whole folders and creates per-file JSON reports.
- Disables project-managed OpenAI/Azure cloud processing by default; enables it only with explicit `--allow-cloud` consent.

## Local-first does not mean network-enforced offline

The application does **not** promise to block every network request from every third-party library. PaddleOCR may download weights on first use. Download dependencies and model weights through approved channels before disconnected deployment. For strict isolation, enforce outbound network restrictions at the OS, container, or network layer; see [SECURITY.md](SECURITY.md).

Basic page-by-page scanned-PDF OCR is implemented with PaddleOCR 3.x, but it has only been verified using synthetic OCR results so far. Real-model testing on representative PDFs is required before production use.

## Quick start (Windows PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

python scripts/convert_one.py input/example.pdf
python scripts/convert_batch.py input --recursive
```

To convert a local image:

```powershell
python scripts/convert_one.py input/example.png
```

To OCR a scanned PDF locally (PaddleOCR 3.x is required):

```powershell
python scripts/convert_one.py input/scanned.pdf --mode paddle_ocr
python scripts/convert_one.py input/scanned.pdf --mode paddle_ocr --offline
```

`--offline` blocks Python socket connections during document conversion. It does not isolate native extensions or separate subprocesses, and does not replace OS or network egress controls. OCR weights and dependencies must be installed beforehand.

**Do not run the examples on confidential corporate files unless the deployment, dependencies, temporary outputs, logs, and network controls are approved by your organization.**

## Cloud processing is opt-in

Standard conversion and image OCR do not require a cloud API key. The fallback pipeline excludes OpenAI and Azure modes unless explicitly enabled.

```powershell
# Only on inputs authorized for external processing:
python scripts/convert_one.py input/public.pdf --mode ocr --allow-cloud
python scripts/convert_batch.py input/public_docs --allow-cloud
```

Cloud modes require separately configured provider credentials and may upload document content. Avoid `--allow-cloud` in sensitive environments.

## Output directories

```text
output/
├── raw_md/      # extracted text
├── clean_md/    # normalized Markdown
├── json_logs/   # conversion metadata
└── failed/      # failed inputs and diagnostic reports
```

In batch conversion, files sharing a stem receive distinct, stable output keys. Other input files retain existing output names; single-file CLI naming remains unchanged.

## Tests

Run fast unit tests:

```powershell
python -m pip install pytest PyYAML
python -m pytest -q tests/test_config_loader.py tests/test_escalator.py tests/test_logger.py tests/test_normalizer.py tests/test_router.py tests/test_validator.py tests/test_cloud_guard.py tests/test_paddle_ocr.py tests/test_offline_network.py tests/test_batch_collisions.py
```

Run the full suite after installing all dependencies:

```powershell
python -m pytest -q
```

## Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md). Use only synthetic or legally redistributable test documents.

## License

[MIT](LICENSE). Third-party libraries and their models have their own licenses.
