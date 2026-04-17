# Skill: 문서 라우팅

## 라우팅 순서
1. 확장자로 1차 판별 → `EXTENSION_MAP`에서 초기 모드 결정
2. 확장자 미매핑 시 `magika`로 MIME 확인
3. MIME도 판별 불가 시 `unknown` → `failed/`로 이동

## 모드 에스컬레이션 흐름
```
standard → (검증 실패) → ocr → (검증 실패) → high_accuracy → (실패) → failed/
```

## PDF 특수 처리
- PDF는 항상 Standard 추출 후 검증 실행
- 검증 기준: char_count ≥ 50, 반복 이상 없음, 추출 비율 ≥ 1%
- 스캔 PDF는 Standard에서 거의 빈 출력 → 자동 OCR 에스컬레이션

## 확장자 → 모드 매핑
settings.yaml의 `modes.extension_overrides`로 특정 확장자의 기본 모드를 재정의 가능:
```yaml
modes:
  extension_overrides:
    ".tif": "ocr"     # TIFF는 바로 OCR
    ".tiff": "ocr"
```
