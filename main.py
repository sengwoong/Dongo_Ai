from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import yaml
import os
import requests
import json
import random

# 디렉토리 생성
os.makedirs("static", exist_ok=True)

app = FastAPI(title="영단어 생성 API", description="Ollama를 사용한 영어 단어 생성 API")

# 정적 파일 마운트
app.mount("/static", StaticFiles(directory="static"), name="static")

# 루트 경로를 HTML 페이지로 리다이렉트

# 요청 모델 정의
class WordRequest(BaseModel):
    word: str
    meaning: str
    vocaId: int
    schoolLevel: Optional[str] = "중등"

class RouletteRequest(BaseModel):
    word: str
    count: Optional[int] = 8

class VocabularyRequest(BaseModel):
    count: Optional[int] = 10
    school_level: Optional[str] = "중등"

class VocabularyItemRequest(BaseModel):
    word: str
    meaning: str

class VocabularyGenerateRequest(BaseModel):
    items: List[VocabularyItemRequest]

# 응답 모델 정의
class WordResponse(BaseModel):
    status: str
    data: Dict[str, Any]

class RouletteItem(BaseModel):
    id: int
    name: str
    color: str
    percentage: int

class RouletteResponse(BaseModel):
    status: str
    data: List[RouletteItem]

class VocabularyItem(BaseModel):
    word: str
    meaning: str
    options: List[str]

class VocabularyResponse(BaseModel):
    status: str
    data: List[VocabularyItem]

# 오류 응답 모델
class ErrorResponse(BaseModel):
    status: str
    message: str

# API 문서 엔드포인트 추가
@app.get("/api-docs", response_model=Dict[str, Any])
async def api_docs():
    """API 문서를 제공하는 엔드포인트"""
    return {
        "api_name": "영단어 생성 API",
        "version": "1.0.0",
        "description": "Ollama를 사용한 영어 단어 생성 API",
        "base_url": "http://localhost:8000",
        "endpoints": [
            {
                "path": "/generate-word",
                "method": "POST",
                "description": "단일 영어 단어 생성",
                "parameters": [
                    {
                        "name": "voca_id",
                        "type": "integer",
                        "description": "단어 난이도 레벨 (1-5)",
                        "required": True
                    },
                    {
                        "name": "school_level",
                        "type": "string",
                        "description": "학교 수준 (초등, 중등, 고등)",
                        "default": "중등",
                        "required": False
                    }
                ],
                "response_example": {
                    "status": "success",
                    "data": {
                        "word": "apple",
                        "meaning": "사과",
                        "vocaId": 1,
                        "schoolLevel": "초등",
                        "id": 1234
                    }
                }
            },
            {
                "path": "/generate-multiple",
                "method": "POST",
                "description": "여러 영어 단어 생성",
                "parameters": [
                    {
                        "name": "voca_id",
                        "type": "integer",
                        "description": "단어 난이도 레벨 (1-5)",
                        "required": True
                    },
                    {
                        "name": "count",
                        "type": "integer",
                        "description": "생성할 단어 개수",
                        "default": 10,
                        "required": False
                    },
                    {
                        "name": "school_level",
                        "type": "string",
                        "description": "학교 수준 (초등, 중등, 고등)",
                        "default": "중등",
                        "required": False
                    }
                ],
                "response_example": {
                    "status": "success",
                    "data": [
                        {
                            "word": "apple",
                            "meaning": "사과",
                            "vocaId": 1,
                            "schoolLevel": "초등",
                            "id": 1234
                        },
                        {
                            "word": "banana",
                            "meaning": "바나나",
                            "vocaId": 1,
                            "schoolLevel": "초등",
                            "id": 1235
                        }
                    ]
                }
            },
            {
                "path": "/generate-roulette",
                "method": "POST",
                "description": "단어를 기반으로 룰렛 아이템 생성",
                "parameters": [
                    {
                        "name": "word",
                        "type": "string",
                        "description": "기준 단어",
                        "required": True
                    },
                    {
                        "name": "count",
                        "type": "integer",
                        "description": "생성할 단어 개수",
                        "default": 8,
                        "required": False
                    }
                ],
                "response_example": {
                    "status": "success",
                    "data": [
                        {"id": 1, "name": "사과", "color": "#E7EFF3", "percentage": 3},
                        {"id": 2, "name": "바나나", "color": "#ffffff", "percentage": 7},
                        {"id": 3, "name": "오렌지", "color": "#E7EFF3", "percentage": 10},
                        {"id": 4, "name": "꽝4", "color": "#ffffff", "percentage": 20},
                        {"id": 5, "name": "꽝5", "color": "#E7EFF3", "percentage": 20},
                        {"id": 6, "name": "꽝6", "color": "#ffffff", "percentage": 20},
                        {"id": 7, "name": "꽝7", "color": "#E7EFF3", "percentage": 10},
                        {"id": 8, "name": "꽝8", "color": "#ffffff", "percentage": 10}
                    ]
                }
            },
            {
                "path": "/generate-vocabulary",
                "method": "POST",
                "description": "단어장 데이터 생성",
                "parameters": [
                    {
                        "name": "count",
                        "type": "integer",
                        "description": "생성할 단어 개수",
                        "default": 10,
                        "required": False
                    },
                    {
                        "name": "school_level",
                        "type": "string",
                        "description": "학교 수준 (초등, 중등, 고등)",
                        "default": "중등",
                        "required": False
                    }
                ],
                "response_example": {
                    "status": "success",
                    "data": [
                        {
                            "word": "apple",
                            "meaning": "사과",
                            "options": ["사과", "바나나", "오렌지", "포도"]
                        },
                        {
                            "word": "book",
                            "meaning": "책",
                            "options": ["책", "연필", "가방", "의자"]
                        }
                    ]
                }
            },
            {
                "path": "/generate-vocabulary-options",
                "method": "POST",
                "description": "단어와 의미를 받아 선택지를 포함한 단어장 항목 생성",
                "parameters": [
                    {
                        "name": "items",
                        "type": "array",
                        "description": "단어와 의미 목록",
                        "required": True,
                        "items": {
                            "word": "string",
                            "meaning": "string"
                        }
                    }
                ],
                "response_example": {
                    "status": "success",
                    "data": [
                        {
                            "word": "apple",
                            "meaning": "사과",
                            "options": ["사과", "바나나", "오렌지", "포도"]
                        },
                        {
                            "word": "book",
                            "meaning": "책",
                            "options": ["책", "연필", "가방", "의자"]
                        }
                    ]
                }
            },
            {
                "path": "/api-docs",
                "method": "GET",
                "description": "API 문서 제공",
                "parameters": [],
                "response_example": "현재 보고 있는 문서"
            }
        ],
        "models": {
            "WordRequest": {
                "properties": {
                    "word": {"type": "string", "description": "영어 단어"},
                    "meaning": {"type": "string", "description": "단어의 한국어 의미"},
                    "vocaId": {"type": "integer", "description": "단어 난이도 레벨"},
                    "schoolLevel": {"type": "string", "description": "학교 수준 (초등, 중등, 고등)"}
                }
            },
            "WordResponse": {
                "properties": {
                    "status": {"type": "string", "description": "응답 상태 (success/error)"},
                    "data": {"type": "object", "description": "응답 데이터"}
                }
            }
        },
        "usage_examples": {
            "curl": [
                "curl -X POST \"http://localhost:8000/generate-word?voca_id=1&school_level=초등\"",
                "curl -X POST \"http://localhost:8000/generate-multiple?voca_id=1&count=5&school_level=중등\""
            ],
            "python": [
                "import requests\n\nresponse = requests.post(\"http://localhost:8000/generate-word\", params={\"voca_id\": 1, \"school_level\": \"초등\"})\nprint(response.json())",
                "import requests\n\nresponse = requests.post(\"http://localhost:8000/generate-multiple\", params={\"voca_id\": 1, \"count\": 5, \"school_level\": \"중등\"})\nprint(response.json())"
            ]
        }
    }

# YAML 설정 로드
def load_config():
    try:
        with open("commands.yaml", "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except Exception as e:
        raise Exception(f"YAML 파일을 로드하는 중 오류가 발생했습니다: {e}")

# Ollama API 호출 함수
def generate_with_ollama(prompt, config):
    try:
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": config["model"]["name"],
            "prompt": prompt,
            "temperature": config["model"]["temperature"],
            "top_p": config["model"]["top_p"],
            "max_tokens": config["model"]["max_tokens"]
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        # Ollama는 스트리밍 응답을 반환하므로 전체 텍스트를 모아야 함
        full_response = ""
        for line in response.text.strip().split('\n'):
            if line:
                data = json.loads(line)
                full_response += data.get("response", "")
                if data.get("done", False):
                    break
        
        return full_response
    except requests.exceptions.ConnectionError:
        raise Exception("Ollama 서버에 연결할 수 없습니다. Ollama가 실행 중인지 확인하세요.")
    except Exception as e:
        raise Exception(f"Ollama API 호출 중 오류 발생: {str(e)}")

# 모의 ID 생성 함수
def generate_mock_id():
    return random.randint(1000, 9999)

# 설정 로드
try:
    config = load_config()
    print("설정이 성공적으로 로드되었습니다.")
    
    # Ollama 서버 연결 테스트
    test_prompt = "Hello"
    generate_with_ollama(test_prompt, config)
    print("Ollama 서버에 성공적으로 연결되었습니다.")
except Exception as e:
    print(f"초기화 중 오류 발생: {e}")
    config = None

@app.post("/generate-multiple", response_model=Dict[str, Any])
async def generate_multiple_words(voca_id: int, count: int = 10, school_level: str = "중등"):
    if config is None:
        raise HTTPException(
            status_code=500,
            detail="설정이 초기화되지 않았습니다."
        )
    
    # 학교 수준 검증
    if school_level not in ["초등", "중등", "고등"]:
        raise HTTPException(
            status_code=400,
            detail="유효하지 않은 학교 수준입니다. '초등', '중등', '고등' 중 하나를 선택하세요."
        )
    
    try:
        # 학교 수준에 따른 난이도 조정
        if school_level == "초등":
            difficulty = "쉬운"
            grade_range = "1-6학년"
        elif school_level == "중등":
            difficulty = "중간"
            grade_range = "7-9학년"
        elif school_level == "고등":
            difficulty = "어려운"
            grade_range = "10-12학년"
        
        # 여러 단어 생성을 위한 프롬프트 개선
        prompt = f"""당신은 영어 단어를 생성하는 AI입니다. 사용자의 지시에 정확히 따라주세요.

{school_level} 학생을 위한 {difficulty} 난이도의 영어 단어와 그 의미를 한국어로 {count}개 생성해주세요. ({grade_range})
난이도 레벨: {voca_id}

각 단어는 반드시 다음 형식으로 작성해주세요:
단어: [영단어]
의미: [한국어 의미]

단어 사이에는 빈 줄을 넣어주세요. 설명이나 추가 텍스트를 포함하지 마세요.

예시:
단어: apple
의미: 사과

단어: book
의미: 책"""
        
        # Ollama로 단어 생성
        generated_text = generate_with_ollama(prompt, config)
        print(f"생성된 텍스트: {generated_text}")  # 디버깅용 로그
        
        # 생성된 텍스트 파싱
        words = []
        current_word = {}
        
        lines = generated_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                if current_word and "word" in current_word and "meaning" in current_word:
                    words.append(current_word)
                    current_word = {}
                continue
                
            if ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    key, value = parts
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == "단어" or key == "word":
                        if current_word and "word" in current_word and "meaning" in current_word:
                            words.append(current_word)
                            current_word = {}
                        current_word["word"] = value
                    elif key == "의미" or key == "meaning":
                        current_word["meaning"] = value
        
        # 마지막 단어 추가
        if current_word and "word" in current_word and "meaning" in current_word:
            words.append(current_word)
        
        # 필요한 수만큼 단어가 생성되었는지 확인
        if len(words) < count:
            # 부족한 경우 추가 생성 시도
            additional_prompt = f"""추가로 {count - len(words)}개의 {school_level} 학생을 위한 {difficulty} 난이도의 영어 단어와 의미를 생성해주세요. ({grade_range})
            난이도 레벨: {voca_id}
            
            각 단어는 다음 형식으로 정확히 작성해주세요:
            단어: [영단어]
            의미: [한국어 의미]
            
            단어 사이에는 빈 줄을 넣어주세요. 다른 설명이나 추가 텍스트 없이 위 형식만 사용해주세요."""
            
            additional_text = generate_with_ollama(additional_prompt, config)
            print(f"추가 생성된 텍스트: {additional_text}")  # 디버깅용 로그
            
            # 추가 파싱 로직 (위와 동일)
            additional_words = []
            current_word = {}
            
            lines = additional_text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    if current_word and "word" in current_word and "meaning" in current_word:
                        additional_words.append(current_word)
                        current_word = {}
                    continue
                    
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        key, value = parts
                        key = key.strip().lower()
                        value = value.strip()
                        
                        if key == "단어" or key == "word":
                            if current_word and "word" in current_word and "meaning" in current_word:
                                additional_words.append(current_word)
                                current_word = {}
                            current_word["word"] = value
                        elif key == "의미" or key == "meaning":
                            current_word["meaning"] = value
            
            # 마지막 단어 추가
            if current_word and "word" in current_word and "meaning" in current_word:
                additional_words.append(current_word)
                
            words.extend(additional_words)
        
        # 단어가 하나도 생성되지 않았을 경우 대체 방법 시도
        if len(words) == 0:
            # 텍스트를 줄 단위로 분석하여 단어와 의미 추출 시도
            lines = generated_text.split('\n')
            for i in range(0, len(lines) - 1, 2):
                if i + 1 < len(lines):
                    word = lines[i].strip()
                    meaning = lines[i + 1].strip()
                    if word and meaning:
                        words.append({"word": word, "meaning": meaning})
        
        # 각 단어에 vocaId와 ID 추가
        for i, word in enumerate(words):
            word["vocaId"] = voca_id
            word["schoolLevel"] = school_level
            word["id"] = generate_mock_id() + i
        
        return {
            "status": "success",
            "data": words[:count]  # 요청한 개수만큼만 반환
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"여러 단어 생성 중 오류 발생: {str(e)}"
        )

@app.post("/generate-vocabulary", response_model=VocabularyResponse)
async def generate_vocabulary(request: VocabularyRequest):
    """단어장 데이터를 생성합니다."""
    if config is None:
        raise HTTPException(
            status_code=500,
            detail="설정이 초기화되지 않았습니다."
        )
    
    try:
        # 학교 수준에 따른 난이도 조정
        school_level = request.school_level
        if school_level == "초등":
            difficulty = "쉬운"
            grade_range = "1-6학년"
        elif school_level == "중등":
            difficulty = "중간"
            grade_range = "7-9학년"
        elif school_level == "고등":
            difficulty = "어려운"
            grade_range = "10-12학년"
        else:
            difficulty = "중간"
            grade_range = "전체"
        
        # 단어장 생성을 위한 프롬프트
        prompt = f"""{school_level} 학생을 위한 {difficulty} 난이도의 영어 단어장을 {request.count}개 생성해주세요. ({grade_range})

각 단어는 다음 형식으로 정확히 작성해주세요:
단어: [영단어]
의미: [한국어 의미]
선택지: [한국어 의미], [오답1], [오답2], [오답3]

단어 사이에는 빈 줄을 넣어주세요. 다른 설명이나 추가 텍스트 없이 위 형식만 사용해주세요.

예시:
단어: apple
의미: 사과
선택지: 사과, 바나나, 오렌지, 포도

단어: book
의미: 책
선택지: 책, 연필, 가방, 의자"""
        
        # Ollama로 단어장 생성
        generated_text = generate_with_ollama(prompt, config)
        print(f"생성된 텍스트: {generated_text}")  # 디버깅용 로그
        
        # 생성된 텍스트 파싱
        vocabulary_items = []
        current_item = {}
        
        lines = generated_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                if current_item and "word" in current_item and "meaning" in current_item and "options" in current_item:
                    vocabulary_items.append(current_item)
                    current_item = {}
                continue
                
            if ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    key, value = parts
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == "단어" or key == "word":
                        if current_item and "word" in current_item and "meaning" in current_item and "options" in current_item:
                            vocabulary_items.append(current_item)
                            current_item = {}
                        current_item["word"] = value
                    elif key == "의미" or key == "meaning":
                        current_item["meaning"] = value
                    elif key == "선택지" or key == "options":
                        options = [opt.strip() for opt in value.split(',')]
                        current_item["options"] = options
        
        # 마지막 단어 추가
        if current_item and "word" in current_item and "meaning" in current_item and "options" in current_item:
            vocabulary_items.append(current_item)
        
        # 필요한 수만큼 단어가 생성되었는지 확인
        if len(vocabulary_items) < request.count:
            # 부족한 경우 추가 생성 시도
            additional_prompt = f"""추가로 {request.count - len(vocabulary_items)}개의 {school_level} 학생을 위한 {difficulty} 난이도의 영어 단어장을 생성해주세요. ({grade_range})
            
각 단어는 다음 형식으로 정확히 작성해주세요:
단어: [영단어]
의미: [한국어 의미]
선택지: [한국어 의미], [오답1], [오답2], [오답3]

단어 사이에는 빈 줄을 넣어주세요. 다른 설명이나 추가 텍스트 없이 위 형식만 사용해주세요."""
            
            additional_text = generate_with_ollama(additional_prompt, config)
            print(f"추가 생성된 텍스트: {additional_text}")  # 디버깅용 로그
            
            # 추가 파싱 로직 (위와 동일)
            additional_items = []
            current_item = {}
            
            lines = additional_text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    if current_item and "word" in current_item and "meaning" in current_item and "options" in current_item:
                        additional_items.append(current_item)
                        current_item = {}
                    continue
                    
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        key, value = parts
                        key = key.strip().lower()
                        value = value.strip()
                        
                        if key == "단어" or key == "word":
                            if current_item and "word" in current_item and "meaning" in current_item and "options" in current_item:
                                additional_items.append(current_item)
                                current_item = {}
                            current_item["word"] = value
                        elif key == "의미" or key == "meaning":
                            current_item["meaning"] = value
                        elif key == "선택지" or key == "options":
                            options = [opt.strip() for opt in value.split(',')]
                            current_item["options"] = options
            
            # 마지막 단어 추가
            if current_item and "word" in current_item and "meaning" in current_item and "options" in current_item:
                additional_items.append(current_item)
                
            vocabulary_items.extend(additional_items)
        
        return {
            "status": "success",
            "data": vocabulary_items[:request.count]  # 요청한 개수만큼만 반환
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"단어장 생성 중 오류 발생: {str(e)}"
        )

@app.post("/generate-vocabulary-options", response_model=VocabularyResponse)
async def generate_vocabulary_options(request: VocabularyGenerateRequest):
    """단어와 의미를 받아 선택지를 포함한 단어장 항목을 생성합니다."""
    if config is None:
        raise HTTPException(
            status_code=500,
            detail="설정이 초기화되지 않았습니다."
        )
    
    try:
        result_items = []
        
        # 각 단어에 대해 선택지 생성
        for item in request.items:
            # 선택지 생성을 위한 프롬프트
            prompt = f"""다음 영어 단어의 의미와 함께 객관식 문제의 선택지를 생성해주세요:
            
단어: {item.word}
의미: {item.meaning}

정답은 "{item.meaning}"이고, 오답 3개를 추가로 생성해주세요.
선택지는 모두 한국어로 작성하고, 쉼표로 구분해주세요.
다른 설명 없이 선택지만 작성해주세요.

예시 출력 형식:
사과, 바나나, 오렌지, 포도"""
            
            # Ollama로 선택지 생성
            generated_text = generate_with_ollama(prompt, config)
            print(f"생성된 텍스트: {generated_text}")  # 디버깅용 로그
            
            # 생성된 텍스트 파싱
            options_text = generated_text.strip()
            options = [opt.strip() for opt in options_text.split(',')]
            
            # 선택지가 4개 미만이면 기본값 추가
            while len(options) < 4:
                options.append(f"선택지{len(options)+1}")
            
            # 선택지가 4개 초과면 잘라내기
            options = options[:4]
            
            # 정답이 선택지에 없으면 추가
            if item.meaning not in options:
                options[0] = item.meaning
            
            # 결과 항목 추가
            result_items.append({
                "word": item.word,
                "meaning": item.meaning,
                "options": options
            })
        
        return {
            "status": "success",
            "data": result_items
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"단어장 선택지 생성 중 오류 발생: {str(e)}"
        )

# 서버 실행
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 