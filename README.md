# Dongo AI - API (최소 가이드)

FastAPI 기반 영어 단어 생성 및 공유 포스트 검색 API.

## 요구사항
- Python 3.8+
- MySQL 8.0+ (DB: `godlife`)
- Ollama (단어 생성 사용 시), Elasticsearch (검색 사용 시)

## 빠른 시작
```bash
cd Dongo_Ai
python -m venv venv
venv\Scripts\activate  # Windows (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt

# (선택) .env
type nul > .env & (
  echo MYSQL_HOST=localhost
  echo MYSQL_PORT=3306
  echo MYSQL_USER=admin
  echo MYSQL_PASSWORD=1234
  echo MYSQL_DATABASE=godlife
  echo OLLAMA_BASE_URL=http://localhost:11434
)

python main.py
# Swagger: http://localhost:8000/docs
```

## 엔드포인트
- 검색
  - GET `/search/posts`
    - 쿼리: `q`(string), `category`(optional), `size`(default 10), `page`(default 1)
    - 예시:
    ```bash
    curl "http://localhost:8000/search/posts?q=grace&page=1&size=10"
    ```

- 단어장
  - POST `/vocabulary/generate`
    ```bash
    curl -X POST "http://localhost:8000/vocabulary/generate" ^
         -H "Content-Type: application/json" ^
         -d "{\"count\":5,\"school_level\":\"중등\"}"
    ```
  - GET `/vocabulary`
    ```bash
    curl "http://localhost:8000/vocabulary?limit=10"
    ```

## 비고
- 검색 사용 시 로컬 ES가 `http://localhost:9200`에서 실행 중이어야 합니다.
- DB 접속 정보는 `config.py` 또는 `.env`로 설정합니다.

## 라이선스
MIT