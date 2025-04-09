import sys
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

# 현재 디렉토리를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 상대 경로로 임포트
from routes.vocabulary_routes import vocabulary_router

# 디렉토리 생성
os.makedirs("static", exist_ok=True)

app = FastAPI(
    title="영단어 생성 API",
    description="Ollama를 사용한 영어 단어 생성 API"
)

# 정적 파일 마운트
app.mount("/static", StaticFiles(directory="static"), name="static")

# 라우터 등록
app.include_router(vocabulary_router)

# 서버 실행
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 