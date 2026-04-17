# SPEC-KIT: File-to-Markdown

## 1. 시스템 아키텍처

```
┌──────────────────────────────────────────────────────────────┐
│                        CLI Layer                             │
│   convert_one.py    convert_batch.py    (향후 MCP 서버)      │
└───────────┬──────────────┬───────────────────────────────────┘
            │              │
┌───────────▼──────────────▼───────────────────────────────────┐
│                    Pipeline Orchestrator                      │
│  ┌──────────┐  ┌────────────┐  ┌───────────┐  ┌───────────┐ │
│  │  Router   │→│  Extractor │→│ Normalizer │→│ Validator  │ │
│  │(확장자/   │  │(MarkItDown)│  │(clean_md)  │  │(품질검증) │ │
│  │ MIME)     │  │            │  │            │  │           │ │
│  └──────────┘  └────────────┘  └───────────┘  └─────┬─────┘ │
│                                                      │       │
│                    ┌─────────────────────────────────┘       │
│                    │ 실패 시                                  │
│              ┌─────▼─────┐                                   │
│              │ Escalator  │ → 다음 모드 재시도 or failed/     │
│              └───────────┘                                   │
│                                                              │
│  ┌───────────┐  ┌──────────────┐                             │
│  │  Logger   │  │ Config Loader│ (settings.yaml)             │
│  │(json_logs)│  └──────────────┘                             │
│  └───────────┘                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. 디렉토리 구조

```
D:\Projects\File-to-markdown\
├── CLAUDE.md
├── RULES.md
├── PRD.md
├── SPEC-KIT.md
├── README.md
├── requirements.txt
├── .gitignore
├── pytest.ini
│
├── config/
│   └── settings.yaml          # 모든 설정값 (임곗값, 경로, 모드 매핑)
│
├── scripts/
│   ├── convert_one.py         # 단일 파일 변환 (전체 파이프라인)
│   ├── convert_batch.py       # 디렉토리 배치 변환
│   ├── normalize_md.py        # Markdown 정규화 (독립 실행 가능)
│   └── validate_md.py         # 출력 검증 (독립 실행 가능)
│
├── f2md/                      # 핵심 로직 패키지
│   ├── __init__.py
│   ├── router.py              # 파일 → 모드 매핑 (확장자 + MIME)
│   ├── extractor.py           # MarkItDown 래퍼 (3-way 모드)
│   ├── normalizer.py          # Markdown 정규화 로직
│   ├── validator.py           # 품질 검증 로직
│   ├── escalator.py           # 모드 에스컬레이션 관리
│   ├── logger.py              # JSON 로그 생성
│   └── config_loader.py       # settings.yaml 파싱
│
├── input/                     # 변환할 원본 파일
│
├── output/
│   ├── raw_md/
│   ├── clean_md/
│   ├── json_logs/
│   └── failed/
│
├── tests/
│   ├── conftest.py
│   ├── test_config_loader.py
│   ├── test_router.py
│   ├── test_extractor.py
│   ├── test_normalizer.py
│   ├── test_validator.py
│   ├── test_escalator.py
│   ├── test_logger.py
│   └── fixtures/              # 테스트용 샘플 파일
│
└── .claude/
    └── skills/
        ├── markitdown-setup.md
        ├── document-routing.md
        ├── normalize-markdown.md
        ├── validate-output.md
        └── batch-processing.md
```

---

## 3. 모듈 명세

### 3.1 router.py — 라우팅

```python
EXTENSION_MAP = {
    ".pdf": "standard",
    ".docx": "standard",
    # ... (전체 목록은 router.py 참조)
}

def route(file_path: Path, cfg: dict | None = None) -> str:
    """확장자 1차 → magika MIME 2차 → 'unknown' 반환."""
```

### 3.2 extractor.py — MarkItDown 래퍼 (3-way 분기)

```python
class Extractor:
    def __init__(self, mode: str = "standard", cfg: dict | None = None):
        if mode == "ocr":
            # enable_plugins=True + llm_client + llm_model
        elif mode == "high_accuracy":
            # docintel_endpoint (Azure Document Intelligence)
        else:  # standard
            # MarkItDown() 기본

    def extract(self, file_path: Path) -> tuple[str, str | None]:
        """(markdown_text, title) 튜플 반환"""
```

### 3.3 normalizer.py — 정규화

처리 순서 (파이프라인):
1. 코드블록(```) UUID 플레이스홀더로 치환 (보호)
2. 후행 공백 제거 (`rstrip` per line)
3. 3줄+ 연속 개행 → 2줄로 축소
4. 불릿 통일 (`*`, `+` → `-`)
5. 빈 헤딩 제거 (`## \n` 같은 것)
6. 반복 토큰 축소 (동일 10자+ 문자열 3회+ 반복 → 1회)
7. 선행/후행 공백행 제거
8. 플레이스홀더 → 코드블록 복원

### 3.4 validator.py — 검증

```python
@dataclass
class ValidationResult:
    passed: bool
    char_count: int
    heading_count: int
    repetition_flag: bool
    extraction_ratio: float | None
    failure_reasons: list[str]
    warnings: list[str]

def validate(clean_md: str, input_size_bytes: int | None = None, cfg: dict | None = None) -> ValidationResult:
```

검증 임곗값은 `config/settings.yaml`에서 로드:
```yaml
validation:
  min_char_count: 50
  max_repetition_count: 5
  repetition_min_length: 10
  min_extraction_ratio: 0.01
```

### 3.5 escalator.py — 에스컬레이션

```python
DEFAULT_MODE_CHAIN = ["standard", "ocr", "high_accuracy"]

def next_mode(current: str, chain: list[str] | None = None) -> str | None:
    """다음 에스컬레이션 모드 반환. 더 이상 없으면 None."""
```

### 3.6 logger.py — 로깅

```python
def write_log(log_dir: Path, log_data: dict) -> Path:
    """JSON 로그 파일 생성. 반환값은 로그 파일 경로."""

def build_log(*, input_file, input_size_bytes, detected_type, ...) -> dict:
    """표준 형식 로그 딕셔너리 생성."""
```

---

## 4. 설정 파일 스키마 (config/settings.yaml)

```yaml
paths:
  input: "input"
  raw_md: "output/raw_md"
  clean_md: "output/clean_md"
  json_logs: "output/json_logs"
  failed: "output/failed"

modes:
  default: "standard"
  chain: ["standard", "ocr", "high_accuracy"]
  max_retries: 3
  extension_overrides:
    ".tif": "ocr"
    ".tiff": "ocr"

ocr:
  llm_model: "gpt-4o"

high_accuracy:
  provider: "azure_doc_intelligence"

validation:
  min_char_count: 50
  max_repetition_count: 5
  repetition_min_length: 10
  min_extraction_ratio: 0.01

normalization:
  bullet_char: "-"
  max_consecutive_newlines: 2

batch:
  max_workers: 4
  continue_on_error: true
```

---

## 5. 전체 파이프라인 흐름 (convert_one.py)

```
1. config/settings.yaml 로드
2. 입력 파일 경로 확인 (존재, 읽기 가능)
3. router.route(path) → 초기 모드 결정
4. Extractor(mode).extract(path) → raw Markdown
5. raw_md/ 에 저장 (절대 덮어쓰지 않음, --force 옵션 제외)
6. normalizer.normalize(raw) → clean Markdown
7. clean_md/ 에 저장
8. validator.validate(clean, input_size) → ValidationResult
9. if 통과:
     - logger.write_log(status="success")
     - 완료
10. if 실패:
     - escalator.next_mode(current) → 다음 모드
     - if 다음 모드 있음: 4번으로 돌아가 재시도
     - if 모드 소진: failed/ 이동 + logger.write_log(status="failed")
```

---

## 6. 의존성

```
# requirements.txt
markitdown[all]>=0.1.0
pyyaml>=6.0
charset-normalizer>=3.0
magika>=0.5.0

# Phase 2 추가
# openai>=1.0        # OCR 모드 LLM Vision
# pymupdf4llm>=0.1   # High-accuracy 대안
```

---

## 7. 테스트 전략

| 레벨 | 대상 | 방법 |
|---|---|---|
| 단위 | router, normalizer, validator, escalator, logger, config_loader | pytest, 인메모리 입력 |
| 통합 | extractor (Standard 모드) | fixtures/ 샘플 파일 (txt, html, csv) |
| 배치 | convert_batch | tmp_path 임시 디렉토리 |
| 회귀 | 정규화 전후 비교 | 스냅샷 테스트 |

테스트 실행:
```powershell
pytest tests\ -v --tb=short
```
