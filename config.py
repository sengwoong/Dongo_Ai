import os
from dotenv import load_dotenv

load_dotenv()

# MySQL 설정
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "admin")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "1234")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "godlife")

# MySQL 연결 문자열
MYSQL_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

# Ollama 설정
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# API 설정
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000)) 