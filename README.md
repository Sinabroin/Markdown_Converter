# File-to-Markdown

MarkItDown을 변환 엔진으로 사용하는 문서 → Markdown 변환 파이프라인.
LLM/RAG 전처리에 바로 투입 가능한 정규화된 Markdown을 생산합니다.

## 특징

- **자동 라우팅**: 확장자/MIME 기반으로 최적 변환 모드 자동 선택
- **3단계 변환**: Standard → OCR → High-accuracy 자동 에스컬레이션
- **원본/정규화 분리**: `raw_md/`(원본 보존) + `clean_md/`(정규화 완료) 분리 저장
- **품질 검증**: 문자 수, 반복 이상, 추출 비율 등 자동 검증
- **변환 로깅**: 변환 1건당 JSON 로그 1개 생성

## 지원 포맷 (Phase 1)

PDF, DOCX, PPTX, XLSX, HTML, CSV, JSON, XML, EPUB, ZIP, JPG/PNG, 플레인텍스트

## 빠른 시작

```powershell
# 1. 가상환경 생성 및 활성화
python -m venv .venv
.venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 단일 파일 변환
python scripts\convert_one.py input\document.pdf

# 4. 디렉토리 일괄 변환
python scripts\convert_batch.py input\ --recursive
```

## 출력 구조

```
output/
├── raw_md/       # MarkItDown 원본 출력 (수정 금지)
├── clean_md/     # 정규화된 최종 Markdown (실제 사용)
├── json_logs/    # 변환별 JSON 로그
└── failed/       # 검증 실패 파일 + 사유 JSON
```

## CLI 명령어

```powershell
# 단일 파일 변환 (전체 파이프라인)
python scripts\convert_one.py input\report.pdf

# 강제 재변환 (raw_md/ 덮어쓰기)
python scripts\convert_one.py input\report.pdf --force

# 배치 변환
python scripts\convert_batch.py input\ --recursive --workers 8

# 정규화만 실행
python scripts\normalize_md.py output\raw_md\report.md

# 검증만 실행
python scripts\validate_md.py output\clean_md\report.md --input-size 204800
```

## 프로젝트 구조

```
File-to-markdown/
├── config/
│   └── settings.yaml       # 모든 설정값
├── f2md/                   # 핵심 로직 패키지
│   ├── config_loader.py
│   ├── router.py
│   ├── extractor.py
│   ├── normalizer.py
│   ├── validator.py
│   ├── escalator.py
│   └── logger.py
├── scripts/
│   ├── convert_one.py      # 단일 파일 변환
│   ├── convert_batch.py    # 배치 변환
│   ├── normalize_md.py     # 정규화 단독 실행
│   └── validate_md.py      # 검증 단독 실행
├── input/                  # 변환할 원본 파일
├── output/                 # 변환 결과물
└── tests/                  # pytest 테스트
```

## 설정

`config/settings.yaml`에서 모든 설정을 관리합니다.

```yaml
validation:
  min_char_count: 50         # 최소 문자 수
  min_extraction_ratio: 0.01 # 최소 추출 비율 (1%)

batch:
  max_workers: 4             # 병렬 변환 워커 수
```

## 환경 변수 (Phase 2 OCR/High-accuracy 모드)

```
F2MD_LLM_API_KEY=sk-...          # OpenAI API 키 (OCR 모드)
F2MD_DOCINTEL_ENDPOINT=https://... # Azure Document Intelligence (고정밀 모드)
```

## 테스트

```powershell
pytest tests\ -v --tb=short
```

## 요구사항

- Python 3.13+
- Windows 10/11 (CMD / PowerShell)
