# Skill: 출력 검증

## 검증 항목

| 항목 | 조건 | 실패 액션 |
|---|---|---|
| 파일 존재 | 출력 파일이 디스크에 있는가 | 즉시 failed/ |
| 비어 있지 않음 | `len(text) > 0` | 즉시 failed/ |
| 최소 길이 | `char_count >= min_char_count` (기본 50) | 모드 에스컬레이션 |
| 헤딩 보존 | 원본에 구조가 있으면 `#` 1개 이상 | 경고 로그 (에스컬레이션 안 함) |
| 반복 이상 | 10자+ 동일 문자열 5회+ 반복 | 모드 에스컬레이션 |
| 추출 비율 | `len(text) / input_size >= 0.01` | 모드 에스컬레이션 |

## 재시도 정책
- 에스컬레이션 순서: standard → ocr → high_accuracy
- 각 모드에서 최대 1회 시도
- 모든 모드 소진 시 → `failed/`에 원본 복사 + 사유 JSON 생성

## 사유 JSON 예시
```json
{
  "input_file": "scan_report.pdf",
  "failure_reasons": ["char_count=12 < min=50", "extraction_ratio=0.002 < min=0.01"],
  "modes_tried": ["standard", "ocr", "high_accuracy"],
  "timestamp": "2026-04-13T16:00:00+09:00"
}
```

## 독립 실행
```powershell
python scripts\validate_md.py output\clean_md\sample.md --input-size 204800
```
