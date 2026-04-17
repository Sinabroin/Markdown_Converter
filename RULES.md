# File-to-Markdown Rules

## 1. 범위
이 프로젝트는 문서→Markdown 변환 파이프라인이다.
목표는 LLM/RAG 전처리에 최적화된 구조적 Markdown 생산이다.
시각적 재현이 아닌 의미·구조 보존에 집중한다.
MarkItDown을 변환 엔진으로 사용하고, 라우팅·정규화·검증을 자체 구현한다.

## 2. 환경
- Python 3.13 프로젝트 로컬 가상환경 사용
- 기존 Python 3.14 환경은 건드리지 않음 (삭제 금지)
- 코딩 전 `python --version`, `pip show markitdown` 으로 버전 확인 필수
- `markitdown[all]`을 설치하고 설치 버전을 로그에 기록

## 3. 파이프라인 원칙
- 원본 추출(raw)과 정규화 결과(clean)를 항상 분리 저장
- raw 출력을 절대 덮어쓰지 않음 (원본 보존)
- 모든 변환에 로그 기록: 모드, 버전, 입력 경로, 출력 경로, 검증 상태
- 스크립트는 기능 단위로 분리 (convert, normalize, validate, batch)
- CLI 진입점은 단순하고 명확하게 유지

## 4. 폴더 구조
```
D:\Projects\File-to-markdown\
├── input/                  # 변환할 원본 파일
├── output/
│   ├── raw_md/            # MarkItDown 원본 출력
│   ├── clean_md/          # 정규화 완료 Markdown
│   ├── json_logs/         # 변환별 JSON 로그
│   └── failed/            # 검증 실패 파일 + 사유 JSON
├── scripts/               # 변환·정규화·검증 스크립트
├── config/                # settings.yaml
├── tests/                 # pytest 테스트
├── .claude/skills/        # Claude Code 스킬 파일
├── CLAUDE.md
├── RULES.md
├── PRD.md
└── SPEC-KIT.md
```

## 5. 라우팅
- 1차 판별: 파일 확장자 기반
- 2차 판별: MIME 타입 확인 (확장자 불명 시)
- PDF는 Standard 추출 후 반드시 품질 검증
- 검증 실패 시 에스컬레이션: Standard → OCR → High-accuracy
- 모든 파일을 최고 비용 경로로 보내지 않음 — 가장 저렴한 경로부터 시도

## 6. 모드 정의
| 모드 | 대상 파일 | 도구/방법 |
|---|---|---|
| Standard | 디지털 PDF, DOCX, PPTX, XLSX, HTML, CSV, JSON, XML, EPUB, ZIP | `markitdown` 기본 |
| OCR | 스캔 PDF, 이미지 중심 문서 | `markitdown` + LLM Vision / OCR 플러그인 |
| High-accuracy | 복잡 레이아웃, 표 중심 | Azure Document Intelligence 또는 pymupdf4llm |

## 7. 정규화
raw Markdown은 중간 산출물이다. 정규화는 다음을 처리한다:
- 후행 공백 제거, 3줄 이상 연속 개행을 2줄로 축소
- 불릿 포맷 통일 (`*`, `+` → `-`)
- 빈 헤딩 제거, 헤딩 레벨 정리 (중간 레벨 건너뛰기 보정)
- 반복 토큰 감지 및 축소 (동일 문장 3회 이상 반복 시 1회로)
- 의미 없는 링크 라벨 (`기사원문` 등) 정리 — URL 날조 금지
- 정규화는 의미를 보존해야 하며, 내용을 생성하지 않음

## 8. 검증
검증은 필수이다. 최소 검증 항목:
| 항목 | 기준 | 실패 시 |
|---|---|---|
| 파일 존재 | output 파일이 생성되었는가 | 즉시 failed/ 이동 |
| 비어 있지 않음 | 문자 수 > 0 | 즉시 failed/ 이동 |
| 최소 길이 | 문자 수 ≥ 50 (빈 문서 제외) | 모드 에스컬레이션 |
| 헤딩 보존 | 원본에 제목 있으면 `#` 1개 이상 존재 | 경고 로그 |
| 반복 이상 | 동일 10자+ 문자열이 5회 이상 반복 | 모드 에스컬레이션 |
| 추출 비율 | 원본 크기 대비 추출 텍스트 비율 < 1% | 모드 에스컬레이션 |
검증 실패는 재시도 또는 `failed/` 라우팅을 트리거한다.

## 9. 로깅
변환 1건당 JSON 로그 1개. 필수 필드:
```json
{
  "input_file": "sample.pdf",
  "input_size_bytes": 204800,
  "detected_type": "pdf",
  "selected_mode": "standard",
  "escalated_to": null,
  "retry_count": 0,
  "markitdown_version": "0.1.1",
  "python_version": "3.13.1",
  "output_raw": "output/raw_md/sample.md",
  "output_clean": "output/clean_md/sample.md",
  "validation": {
    "char_count": 3842,
    "heading_count": 5,
    "repetition_flag": false,
    "passed": true
  },
  "duration_seconds": 1.23,
  "status": "success",
  "timestamp": "2026-04-13T15:30:00+09:00"
}
```

## 10. 문서 관리
- PRD는 구현 전에 작성
- SPEC-KIT는 코딩 전에 작성
- 아키텍처 변경 시 PRD/SPEC-KIT/RULES 동시 업데이트
- CLAUDE.md는 짧고 전략적으로 유지, 반복 절차는 스킬에 위임

## 11. 코딩 규칙
- 스크립트별 단일 책임: convert_one, convert_batch, normalize_md, validate_md
- 설정값(임곗값, 경로, 모드 매핑)은 `config/settings.yaml`에 분리
- 비즈니스 로직에 매직넘버 금지
- 함수 단위로 명확한 입출력 경계
- Windows 경로 처리: `pathlib.Path` 사용 필수 (`os.path.join` 지양)

## 12. 운영자 경험
- 대상 환경: Windows CMD / PowerShell
- 항상 실행 가능한 정확한 명령어 제공
- 실행 후 즉시 확인할 수 있는 검증 명령어 함께 제공
- 숨은 전제 조건 없이 자체 완결적 안내

## 13. 비범위
- SaaS, 멀티유저 인증, 과금, 대시보드는 초기 범위 아님
- 먼저 변환 파이프라인을 견고하게 만든 후, 필요 시 UI/서비스 계층 추가
- 픽셀 단위 문서 재현은 목표가 아님
