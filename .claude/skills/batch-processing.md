# Skill: 배치 처리

## 실행
```powershell
python scripts\convert_batch.py input\ --recursive
python scripts\convert_batch.py input\ --recursive --workers 4
```

## 동작 방식
1. 입력 디렉토리에서 대상 파일 목록 수집 (재귀 옵션 지원)
2. 각 파일에 대해 `convert_one` 파이프라인 실행
3. 개별 실패가 전체를 중단시키지 않음 (`continue_on_error: true`)
4. 진행률 표시: `[3/25] Converting report.pdf... OK`

## 병렬 처리
- `concurrent.futures.ThreadPoolExecutor` 사용
- `max_workers`는 settings.yaml에서 설정 (기본 4)
- 파일 I/O 바운드이므로 스레드 풀이 적합

## 배치 리포트
완료 후 요약 출력:
```
=== Batch Complete ===
Total: 25
Success: 22
Failed: 3
  - scan_doc.pdf (extraction_ratio too low)
  - corrupt.docx (conversion error)
  - unknown.xyz (unsupported format)
Logs: output\json_logs\
```

## 중복 방지
- `raw_md/`에 동일 이름 파일이 이미 있으면 스킵 (--force로 재변환)
- 로그에 `skipped` 상태 기록
