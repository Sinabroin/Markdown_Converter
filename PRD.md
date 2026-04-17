# PRD: File-to-Markdown

## 1. 개요

**프로젝트명:** File-to-Markdown
**한 줄 요약:** MarkItDown을 변환 엔진으로 쓰고, 라우팅·정규화·검증·로깅 파이프라인을 감싸서 LLM/RAG에 즉시 투입 가능한 Markdown을 생산하는 Windows CLI 도구.

---

## 2. 문제 정의

MarkItDown은 다양한 파일을 Markdown으로 변환하지만, 그 자체로는 프로덕션 파이프라인이 아니다.

| 문제 | 설명 |
|---|---|
| 품질 편차 | 스캔 PDF, 이미지 PDF에서 빈 출력이나 깨진 구조 발생 |
| 후처리 부재 | 과도한 공백, 반복 토큰, 깨진 헤딩이 그대로 나옴 |
| 검증 없음 | 변환 성공/실패를 판단할 기준이 없음 |
| 추적 불가 | 어떤 파일이 어떤 모드로 변환되었는지 로그가 없음 |
| 수동 에스컬레이션 | OCR이나 고정밀 모드로 전환하려면 사용자가 직접 판단 |

**이 파이프라인이 해결하는 것:** 자동 라우팅, 품질 검증, 실패 시 모드 에스컬레이션, 원본/정규화 분리 저장, 전 과정 로깅.

---

## 3. 타겟 사용자

| 사용자 | 니즈 |
|---|---|
| RAG 파이프라인 구축자 | 대량 문서를 전처리해서 벡터 DB에 넣어야 함 |
| LLM 활용 개발자 | 보고서·계약서를 Markdown으로 변환 후 프롬프트에 삽입 |
| 사내 지식관리 담당 | 레거시 문서를 검색 가능한 Markdown으로 마이그레이션 |
| 1인 개발자/연구자 | Windows에서 CLI로 빠르게 문서를 변환 |

---

## 4. 지원 포맷

### Phase 1 (MVP)
PDF, DOCX, PPTX, XLSX, HTML, CSV, JSON, XML, EPUB, ZIP, 이미지(JPG/PNG), 플레인텍스트

### Phase 2 (확장)
- 오디오(MP3/WAV) → Whisper 전사
- URL → 웹 스크래핑 후 변환
- HWP/HWPX → 한글 문서 지원

---

## 5. 핵심 기능

### 5.1 자동 라우팅
- 확장자 기반 1차 판별 → MIME 기반 2차 판별
- 포맷에 따라 Standard / OCR / High-accuracy 모드 자동 선택

### 5.2 3단계 변환 모드
```
Standard (저비용) → 검증 실패 → OCR (중비용) → 검증 실패 → High-accuracy (고비용)
```
- Standard: `markitdown` 기본 변환
- OCR: `markitdown` + LLM Vision 또는 markitdown-ocr 플러그인
- High-accuracy: Azure Document Intelligence 또는 pymupdf4llm

### 5.3 원본/정규화 분리
- `raw_md/`: MarkItDown 원본 출력 (절대 수정하지 않음)
- `clean_md/`: 정규화 완료 Markdown (후행 공백, 반복 토큰, 헤딩 정리)

### 5.4 자동 검증
- 파일 존재, 비어 있지 않음, 최소 길이, 헤딩 보존, 반복 이상, 추출 비율
- 실패 시 자동 에스컬레이션 또는 `failed/` 이동

### 5.5 변환 로깅
- 변환 1건당 JSON 로그 1개
- 입력 파일, 감지 타입, 모드, 재시도 횟수, 버전, 검증 결과, 소요 시간

### 5.6 배치 처리
- 디렉토리 단위 일괄 변환
- 진행률 표시, 실패 파일 요약 리포트

---

## 6. CLI 인터페이스

```powershell
# 단일 변환
python scripts\convert_one.py input\report.pdf

# 배치 변환
python scripts\convert_batch.py input\ --recursive

# 정규화만
python scripts\normalize_md.py output\raw_md\report.md

# 검증만
python scripts\validate_md.py output\clean_md\report.md

# 전체 파이프라인 (변환+정규화+검증)
python scripts\convert_one.py input\report.pdf --full-pipeline
```

---

## 7. 비기능 요구사항

| 항목 | 기준 |
|---|---|
| 성능 | 100페이지 디지털 PDF Standard 변환 < 5초 |
| 환경 | Windows 10/11, Python 3.13, CMD/PowerShell |
| 설정 | 임곗값·경로·모드 매핑은 `config/settings.yaml`에 분리 |
| 에러 처리 | 개별 파일 실패가 배치 전체를 중단시키지 않음 |
| 재현성 | 동일 입력 + 동일 설정 → 동일 출력 (LLM 모드 제외) |

---

## 8. 성공 지표

| 지표 | 목표 |
|---|---|
| Phase 1 포맷 커버리지 | 12개 포맷 Standard 모드 지원 |
| Standard 변환 성공률 | 디지털 문서 95%+ |
| 검증 통과율 | 정규화 후 90%+ |
| 파이프라인 추적성 | 모든 변환에 JSON 로그 100% |

---

## 9. 마일스톤

| 단계 | 내용 | 예상 기간 |
|---|---|---|
| M1 | 프로젝트 스캐폴딩, 환경 구성, settings.yaml | 반나절 |
| M2 | convert_one.py (Standard 모드 + raw 저장) | 1일 |
| M3 | normalize_md.py (정규화 모듈) | 1일 |
| M4 | validate_md.py (검증 + 에스컬레이션) | 1일 |
| M5 | convert_batch.py (배치 + 진행률 + 리포트) | 1일 |
| M6 | OCR / High-accuracy 모드 통합 | 2일 |
| M7 | 테스트, 문서화, 최종 정리 | 1일 |

---

## 10. 비범위
- GUI, 웹 UI, SaaS, 멀티유저 인증
- 픽셀 단위 문서 재현
- 실시간 협업
- DRM 보호 문서
