# File-to-Markdown — CLAUDE.md

## Mission
MarkItDown을 변환 엔진으로 쓰고, 그 위에 라우팅·정규화·검증·로깅 파이프라인을 구축한다.
목표는 LLM/RAG 전처리에 바로 쓸 수 있는 구조적 Markdown 생산이다.
MarkItDown 원본 출력은 중간 산출물이며, 최종 산출물이 아니다.

## 사용자 환경
- OS: Windows (CMD / PowerShell)
- 프로젝트 루트: `D:\Projects\File-to-markdown`
- Python: 3.13 가상환경 사용 (기존 3.14 환경은 건드리지 않음)
- 명령어는 항상 Windows 기준으로 제공할 것

## 파이프라인 흐름
```
입력 파일 → 라우터(확장자/MIME) → 모드 선택 → MarkItDown 추출
→ raw_md/ 저장 → 정규화 → clean_md/ 저장 → 검증
→ 통과 시 완료 + json_logs/ | 실패 시 모드 에스컬레이션 or failed/
```

## 모드
| 모드 | 대상 | 비용 |
|---|---|---|
| Standard | 디지털 PDF, DOCX, PPTX, XLSX, HTML, CSV, JSON, XML, EPUB, ZIP | 낮음 |
| OCR | 스캔/이미지 중심 문서 | 중간 |
| High-accuracy | 복잡한 레이아웃, 표 중심 문서 | 높음 |
기본은 Standard → 검증 실패 시 OCR → 여전히 실패 시 High-accuracy로 에스컬레이션.

## 출력 구조
```
output/
├── raw_md/       # MarkItDown 원본 출력 (수정 금지)
├── clean_md/     # 정규화된 최종 Markdown
├── json_logs/    # 변환별 JSON 로그
└── failed/       # 검증 실패 파일 + 사유
```

## 빌드 & 실행
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt        # markitdown[all] 포함
python scripts\convert_one.py input\sample.pdf
python scripts\convert_batch.py input\ --recursive
pytest tests\ -v
```

## 모듈 구조
- `scripts/convert_one.py` — 단일 파일 변환
- `scripts/convert_batch.py` — 일괄 변환
- `scripts/normalize_md.py` — Markdown 정규화
- `scripts/validate_md.py` — 출력 검증
- `config/settings.yaml` — 임곗값·경로·모드 설정

## 전달 순서
1. PRD → 2. SPEC-KIT → 3. 폴더/파일 스캐폴딩 → 4. 환경 구성
5. 변환 스크립트 → 6. 정규화 → 7. 검증 → 8. 배치 처리 → 9. OCR/고정밀 모드

## 스킬 위임 (상세 절차는 스킬 파일 참조)
- `.claude/skills/markitdown-setup.md` — 환경 구성·버전 확인
- `.claude/skills/document-routing.md` — 확장자·MIME 라우팅 로직
- `.claude/skills/normalize-markdown.md` — 정규화 규칙 상세
- `.claude/skills/validate-output.md` — 검증 기준·재시도 정책
- `.claude/skills/batch-processing.md` — 배치 변환·병렬 처리

## 작업 원칙
- 추상적 설명 전에 실행 가능한 명령어를 먼저 제시
- 대규모 작업은 단계별 산출물로 분할
- PRD/SPEC-KIT 변경 시 반드시 사전 확인
