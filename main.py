import sys
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 현재 디렉토리를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 상대 경로로 임포트
from routes.vocabulary_routes import vocabulary_router
from models.database import create_tables

# 디렉토리 생성
os.makedirs("static", exist_ok=True)

# 데이터베이스 테이블 생성
create_tables()

app = FastAPI(
    title="Dongo AI - 영어 단어 생성 API",
    description="""
    ## Dongo AI 영어 단어 생성 API
    
    Ollama를 사용하여 영어 단어와 단어장을 생성하는 API입니다.
    
    ### 주요 기능:
    - **단어장 생성**: 학교 수준에 맞는 영어 단어장 자동 생성
    - **선택지 생성**: 단어에 대한 객관식 선택지 생성
    - **단어장 관리**: MySQL을 통한 단어장 저장 및 조회
    
    ### 사용 방법:
    1. `/vocabulary/generate` - 단어장 생성
    2. `/vocabulary/generate-options` - 선택지 포함 단어장 생성
    3. `/vocabulary` - 저장된 단어장 조회
    
    ### 학교 수준:
    - `초등학교`: 3-6학년 수준의 쉬운 단어
    - `중학교`: 1-3학년 수준의 중간 난이도 단어
    - `고등학교`: 1-3학년 수준의 어려운 단어
    
    ### 데이터베이스:
    - **MySQL**: 단어장 데이터 저장
    - **연결 정보**: localhost:3306/godlife
    """,
    version="1.0.0",
    contact={
        "name": "Dongo AI Team",
        "email": "support@dongo.ai",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 정적 파일 마운트
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발환경에서는 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(vocabulary_router)

# 커스텀 OpenAPI 스키마 생성
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # 추가 정보 설정
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# 서버 실행
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["routes", "services", "models", "utils"],
        reload_excludes=[
            "logs/*",
            "*.log",
            "static/*",
            "**/__pycache__/**",
            "**/*.pyc",
            "**/*.pyo",
            "**/*.tmp",
        ],
    )