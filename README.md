# Dongo AI - 영어 단어 생성 API

Ollama를 사용하여 영어 단어와 단어장을 동적으로 생성하는 FastAPI 기반 REST API입니다.

## 🚀 주요 기능

- **AI 기반 동적 단어장 생성**: 학교 수준에 맞는 영어 단어 자동 생성
- **동적 객관식 선택지 생성**: 단어에 대한 객관식 문제 자동 생성
- **자동 재시도 로직**: 실패 시 최대 3회 자동 재시도
- **단어장 관리**: MySQL을 통한 단어장 저장 및 조회
- **학교 수준별 난이도**: 초등학교, 중학교, 고등학교 수준별 단어 생성

## 🔄 동적 생성 및 재시도 시스템

### 동적 생성 기능
- **하드코딩 제거**: 모든 단어와 선택지가 AI 모델을 통해 동적으로 생성
- **다양한 형식 지원**: 여러 형식의 AI 응답을 자동으로 파싱
- **유연한 파싱**: 정규표현식을 사용한 강력한 텍스트 파싱

### 재시도 로직
- **최대 3회 재시도**: API 호출 실패 시 자동으로 최대 3회 재시도
- **지능적 대기**: 재시도 간 적절한 대기 시간으로 서버 부하 방지
- **상세한 에러 처리**: 각 시도마다 구체적인 에러 메시지 제공

### 에러 처리
- **연결 오류**: Ollama 서버 연결 실패 시 재시도
- **시간 초과**: 요청 시간 초과 시 재시도
- **빈 응답**: 빈 응답 수신 시 재시도
- **파싱 실패**: 응답 파싱 실패 시 재시도

## 📋 요구사항

- Python 3.8+
- MySQL 8.0+
- Ollama (로컬 AI 모델)

## 🛠️ 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd Dongo_Ai
```

### 2. 가상환경 생성 및 활성화
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 가상환경 활성화 (Mac/Linux)
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. MySQL 설정
```bash
# MySQL 서버 실행
mysql.server start  # Mac
# 또는
sudo systemctl start mysql  # Linux
# 또는
net start mysql  # Windows

# MySQL 접속
mysql -u root -p

# 데이터베이스 생성
CREATE DATABASE godlife CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 사용자 생성 및 권한 부여
CREATE USER 'admin'@'localhost' IDENTIFIED BY '1234';
GRANT ALL PRIVILEGES ON godlife.* TO 'admin'@'localhost';
FLUSH PRIVILEGES;
```

### 5. 환경변수 설정 (선택사항)
```bash
# .env 파일 생성
cat > .env << EOF
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=admin
MYSQL_PASSWORD=1234
MYSQL_DATABASE=godlife
OLLAMA_BASE_URL=http://localhost:11434
EOF
```

### 6. Ollama 실행
```bash
# Ollama가 설치되어 있어야 합니다
ollama serve
```

### 7. 서버 실행
```bash
python main.py
```

서버가 실행되면 다음 URL에서 접근할 수 있습니다:
- **API 문서**: http://localhost:8000/docs
- **ReDoc 문서**: http://localhost:8000/redoc
- **OpenAPI 스키마**: http://localhost:8000/openapi.json

## 📚 API 엔드포인트

### 1. 단어장 생성 (동적 생성 + 재시도)
```http
POST /vocabulary/generate
```

**요청 예시:**
```json
{
  "count": 10,
  "school_level": "중등",
  "userId": "user123",
  "vocaId": "voca456"
}
```

**응답 예시:**
```json
{
  "status": "success",
  "data": [
    {
      "word": "apple",
      "meaning": "사과",
      "options": []
    }
  ]
}
```

### 2. 선택지 포함 단어장 생성 (동적 생성 + 재시도)
```http
POST /vocabulary/generate-options
```

**요청 예시:**
```json
{
  "items": [
    {"word": "apple", "meaning": "사과"},
    {"word": "book", "meaning": "책"}
  ],
  "userId": "user123",
  "vocaId": "voca456"
}
```

**응답 예시:**
```json
{
  "status": "success",
  "data": [
    {
      "word": "apple",
      "meaning": "사과",
      "options": ["사과", "바나나", "오렌지", "포도"]
    }
  ]
}
```

### 3. 단어장 조회
```http
GET /vocabulary?userId=user123&vocaId=voca456&limit=10&skip=0
```

**응답 예시:**
```json
{
  "status": "success",
  "count": 2,
  "data": [
    {
      "word": "apple",
      "meaning": "사과",
      "options": ["사과", "바나나", "오렌지", "포도"],
      "userId": "user123",
      "vocaId": "voca456",
      "createdAt": "2024-01-01T00:00:00"
    }
  ]
}
```

## 🏫 학교 수준별 난이도

| 학교 수준 | 난이도 | 대상 학년 | 설명 |
|-----------|--------|-----------|------|
| 초등학교 | 쉬움 | 3-6학년 | 기초적인 일상 단어 |
| 중학교 | 중간 | 1-3학년 | 중급 수준의 단어 |
| 고등학교 | 어려움 | 1-3학년 | 고급 수준의 단어 |

## 🗂️ 프로젝트 구조

```
Dongo_Ai/
├── model/                    # 데이터 모델
│   ├── EnglishModels.py     # API 요청/응답 모델
│   └── database.py          # MySQL 데이터베이스 모델
├── routes/                   # API 라우터
│   └── vocabulary_routes.py # 단어장 관련 API
├── services/                 # 비즈니스 로직
│   └── problemgeneration_service.py
├── utils/                    # 유틸리티 함수
│   └── __init__.py          # 유틸리티 함수 export
├── yml/                      # 설정 파일
├── static/                   # 정적 파일
├── main.py                   # 메인 애플리케이션
├── config.py                 # 설정 파일
├── utils.py                  # 동적 생성 및 재시도 로직
├── test_dynamic_generation.py # 테스트 스크립트
├── requirements.txt          # 의존성 목록
└── README.md                # 프로젝트 문서
```

## 🗄️ 데이터베이스 스키마

### vocabulary_items 테이블
```sql
CREATE TABLE vocabulary_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    word VARCHAR(100) NOT NULL,
    meaning VARCHAR(200) NOT NULL,
    options TEXT,
    userId VARCHAR(50) NOT NULL,
    vocaId VARCHAR(50) NOT NULL,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_word (word),
    INDEX idx_userId (userId),
    INDEX idx_vocaId (vocaId)
);
```

### vocabularies 테이블
```sql
CREATE TABLE vocabularies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vocaId VARCHAR(50) UNIQUE NOT NULL,
    userId VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    schoolLevel VARCHAR(20) DEFAULT '중등',
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_vocaId (vocaId),
    INDEX idx_userId (userId)
);
```

## 🔧 설정

### MySQL 설정
기본적으로 `localhost:3306/godlife`에 연결됩니다.
필요한 경우 `config.py`에서 연결 정보를 수정하세요.

### Ollama 설정
`EnglishCommand.yaml` 파일에서 Ollama 모델 설정을 확인하고 수정하세요.

## 🧪 테스트

### 동적 생성 기능 테스트
```bash
# 테스트 스크립트 실행
python test_dynamic_generation.py
```

### Swagger UI를 통한 테스트
1. http://localhost:8000/docs 접속
2. 원하는 API 엔드포인트 선택
3. "Try it out" 버튼 클릭
4. 파라미터 입력 후 "Execute" 버튼 클릭

### curl을 통한 테스트
```bash
# 단어장 생성
curl -X POST "http://localhost:8000/vocabulary/generate" \
     -H "Content-Type: application/json" \
     -d '{"count": 5, "school_level": "중등"}'

# 단어장 조회
curl -X GET "http://localhost:8000/vocabulary?limit=10"
```

## 🐛 문제 해결

### MySQL 연결 오류
- MySQL이 실행 중인지 확인
- 데이터베이스와 사용자가 생성되었는지 확인
- 연결 문자열이 올바른지 확인

### Ollama 연결 오류
- Ollama가 실행 중인지 확인
- `EnglishCommand.yaml` 설정 확인

### 재시도 로직 관련
- **3회 재시도 후 실패**: Ollama 서버 상태 확인
- **빈 응답 수신**: AI 모델 설정 확인
- **파싱 실패**: AI 응답 형식 확인

### 의존성 설치 오류
```bash
# 캐시 삭제 후 재설치
pip cache purge
pip install -r requirements.txt --no-cache-dir
```

### 데이터베이스 테이블 생성 오류
```bash
# MySQL 접속 후 테이블 확인
mysql -u admin -p godlife
SHOW TABLES;
```

## 📝 라이선스

MIT License

## 🤝 기여

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 문의

- 이메일: support@dongo.ai
- 프로젝트 이슈: GitHub Issues

---

**Dongo AI Team** - 영어 학습을 더욱 스마트하게! 