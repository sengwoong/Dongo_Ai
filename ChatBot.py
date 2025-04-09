from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import yaml
import os
import requests
import json

app = FastAPI(title="영단어 생성 API", description="Ollama를 사용한 영어 단어 생성 API")

# 요청 모델 정의
class WordRequest(BaseModel):
    word: str
    meaning: str
    vocaId: int

# 응답 모델 정의
class WordResponse(BaseModel):
    status: str
    data: Dict[str, Any]

# 오류 응답 모델
class ErrorResponse(BaseModel):
    status: str
    message: str

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

@app.post("/generate-word", response_model=WordResponse)
async def generate_word(voca_id: int):
    if config is None:
        raise HTTPException(
            status_code=500,
            detail="설정이 초기화되지 않았습니다."
        )
    
    try:
        # 단어 생성을 위한 프롬프트 생성
        prompt = f"초중고 학생을 위한 영어 단어와 그 의미를 한국어로 생성해주세요. 난이도 레벨: {voca_id}"
        
        # Ollama로 단어 생성
        generated_text = generate_with_ollama(prompt, config)
        
        # 생성된 텍스트 파싱 (예: "단어: apple, 의미: 사과")
        try:
            lines = generated_text.split('\n')
            word_data = {}
            
            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == "단어" or key == "word":
                        word_data["word"] = value
                    elif key == "의미" or key == "meaning":
                        word_data["meaning"] = value
            
            # 필수 필드 확인
            if "word" not in word_data or "meaning" not in word_data:
                raise ValueError("생성된 텍스트에서 단어 또는 의미를 찾을 수 없습니다.")
            
            # vocaId 추가
            word_data["vocaId"] = voca_id
            
            # ID 추가 (실제 DB 저장 시에는 생성된 ID 사용)
            word_data["id"] = generate_mock_id()
            
            return {
                "status": "success",
                "data": word_data
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"생성된 텍스트 파싱 중 오류 발생: {str(e)}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"단어 생성 중 오류 발생: {str(e)}"
        )

@app.post("/generate-multiple", response_model=Dict[str, Any])
async def generate_multiple_words(voca_id: int, count: int = 10):
    if config is None:
        raise HTTPException(
            status_code=500,
            detail="설정이 초기화되지 않았습니다."
        )
    
    try:
        # 여러 단어 생성을 위한 프롬프트
        prompt = f"초중고 학생을 위한 영어 단어와 그 의미를 한국어로 {count}개 생성해주세요. 난이도 레벨: {voca_id}. 각 단어는 '단어: [영단어], 의미: [한국어 의미]' 형식으로 작성해주세요."
        
        # Ollama로 단어 생성
        generated_text = generate_with_ollama(prompt, config)
        
        # 생성된 텍스트 파싱
        words = []
        current_word = {}
        
        lines = generated_text.split('\n')
        for line in lines:
            if not line.strip():
                if current_word and "word" in current_word and "meaning" in current_word:
                    words.append(current_word)
                    current_word = {}
                continue
                
            if ":" in line:
                key, value = line.split(":", 1)
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
            additional_prompt = f"추가로 {count - len(words)}개의 영어 단어와 의미를 생성해주세요. 난이도 레벨: {voca_id}"
            additional_text = generate_with_ollama(additional_prompt, config)
            
            # 추가 파싱 로직 (위와 동일)
            additional_words = []
            current_word = {}
            
            lines = additional_text.split('\n')
            for line in lines:
                if not line.strip():
                    if current_word and "word" in current_word and "meaning" in current_word:
                        additional_words.append(current_word)
                        current_word = {}
                    continue
                    
                if ":" in line:
                    key, value = line.split(":", 1)
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
        
        # 각 단어에 vocaId와 ID 추가
        for i, word in enumerate(words):
            word["vocaId"] = voca_id
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

# 모의 ID 생성 함수 (실제 구현에서는 DB에서 생성된 ID 사용)
def generate_mock_id():
    import random
    return random.randint(1000, 9999)

# 서버 실행
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
