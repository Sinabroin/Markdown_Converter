# Skill: MarkItDown 환경 구성

## 최초 환경 세팅

```powershell
cd D:\Projects\File-to-markdown
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install "markitdown[all]" pyyaml charset-normalizer magika
pip show markitdown          # 설치 버전 확인 → 로그에 기록
python --version             # 3.13.x 확인
```

## 버전 고정
```powershell
pip freeze > requirements.txt
```

## 검증 명령
```powershell
python -c "from markitdown import MarkItDown; print('OK')"
python -c "import yaml; print('PyYAML OK')"
python -c "from magika import Magika; print('Magika OK')"
```

## 주의
- Python 3.14 환경은 건드리지 않음
- `markitdown[all]`은 모든 선택 의존성(pdf, docx, pptx 등)을 포함
- 추후 OCR 모드 시 `pip install openai` 추가 필요
