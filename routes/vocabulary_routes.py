import sys
import os
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# 현재 디렉토리의 상위 디렉토리를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 상대 경로로 임포트
from model.EnglishModels import (
    VocabularyRequest, VocabularyGenerateRequest, VocabularyResponse
)
from utils.ollama_utils import generate_with_ollama, load_config

# vocabulary_service.py 파일이 없으므로 필요한 함수를 직접 정의합니다
# 이 함수들은 원래 services.vocabulary_service에 있었을 것입니다

async def generate_and_parse_vocabulary(prompt, count):
    """단어장을 생성하고 파싱합니다."""
    try:
        # services.problemgeneration_service에서 단어장 생성 함수 호출
        from services.problemgeneration_service import generate_vocabulary
        
        # 실제 단어장 생성 함수 호출
        vocabulary_items = generate_vocabulary()
        
        # 생성된 항목 수가 요청한 수보다 적으면 추가 생성
        if len(vocabulary_items) < count:
            additional_items = [
                {"word": f"word{i}", "meaning": f"의미{i}", "example": f"This is example {i}", 
                 "options": [f"옵션{j}" for j in range(4)]} 
                for i in range(len(vocabulary_items), count)
            ]
            vocabulary_items.extend(additional_items)
        
        # 요청한 수만큼만 반환
        return vocabulary_items[:count]
    except Exception as e:
        print(f"단어장 생성 중 오류 발생: {str(e)}")
        # 오류 발생 시 임시 데이터 반환
        return [{"word": f"word{i}", "meaning": f"의미{i}", "example": f"This is example {i}", 
                "options": [f"옵션{j}" for j in range(4)]} for i in range(count)]

def get_difficulty_settings(school_level):
    """학교 수준에 따른 난이도 설정을 반환합니다."""
    # 임시 구현
    difficulty = "중간"
    grade_range = "1-3학년"
    if school_level == "초등학교":
        difficulty = "쉬움"
        grade_range = "3-6학년"
    elif school_level == "중학교":
        difficulty = "중간"
        grade_range = "1-3학년"
    elif school_level == "고등학교":
        difficulty = "어려움"
        grade_range = "1-3학년"
    return difficulty, grade_range

def create_vocabulary_item(item, options, userId, vocaId):
    """단어장 항목을 생성합니다."""
    # 임시 구현
    return {
        "word": item.word,
        "meaning": item.meaning,
        "options": options,
        "userId": userId,
        "vocaId": vocaId,
        "createdAt": datetime.datetime.now()
    }

async def save_vocabulary_items(items):
    """단어장 항목을 저장합니다."""
    # 임시 구현
    for item in items:
        await vocabulary_collection.insert_one(item)
    return True

def prepare_response_items(items):
    """응답용 항목을 준비합니다."""
    # 임시 구현
    return [{
        "word": item["word"],
        "meaning": item["meaning"],
        "options": item["options"]
    } for item in items]

def create_filter_condition(userId, vocaId):
    """필터 조건을 생성합니다."""
    # 임시 구현
    filter_condition = {}
    if userId:
        filter_condition["userId"] = userId
    if vocaId:
        filter_condition["vocaId"] = vocaId
    return filter_condition

async def fetch_vocabulary_items(filter_condition, limit, skip):
    """단어장 항목을 조회합니다."""
    # 임시 구현
    cursor = vocabulary_collection.find(filter_condition).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)

vocabulary_router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])
config = load_config()

# MongoDB 연결 설정
MONGO_URL = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_URL)
db = client.vocabulary_db
vocabulary_collection = db.vocabulary_items


@vocabulary_router.post("/generate", response_model=VocabularyResponse)
async def generate_vocabulary(request: VocabularyRequest):
    """단어장 데이터를 생성합니다."""
    try:
        # 서비스 계층에서 단어장 생성 함수 직접 호출
        from services.problemgeneration_service import generate_vocabulary
        
        # 단어장 생성 (EnglishCommand.yaml 설정에 따라 자동으로 처리됨)
        vocabulary_items = generate_vocabulary()
        
        # 요청한 수만큼만 반환하도록 제한
        requested_count = request.count if request.count else 10
        if len(vocabulary_items) > requested_count:
            vocabulary_items = vocabulary_items[:requested_count]
        
        # 생성된 항목 수가 요청한 수보다 적으면 오류 발생
        if len(vocabulary_items) < requested_count:
            error_msg = f"요청한 {requested_count}개 단어를 생성하지 못했습니다. 생성된 단어: {len(vocabulary_items)}개"
            print(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        
        # 응답 데이터 형식으로 변환
        formatted_items = []
        for item in vocabulary_items:
            formatted_item = {
                "word": item["word"],
                "meaning": item["meaning"],  # 이미 발음 표기 제거됨
                "options": []  # 이 시점에서는 선택지 없음
            }
            formatted_items.append(formatted_item)
        
        return {
            "status": "success",
            "data": formatted_items
        }
    except Exception as e:
        error_msg = f"단어장 생성 중 오류 발생: {str(e)}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)

@vocabulary_router.post("/generate-options", response_model=VocabularyResponse)
async def generate_vocabulary_options(request: VocabularyGenerateRequest):
    """단어와 의미를 받아 선택지를 포함한 단어장 항목을 생성합니다."""
    if not request.userId or not request.vocaId:
        raise HTTPException(status_code=400, detail="userId와 vocaId는 필수 항목입니다.")
    
    try:
        # 상대 경로로 임포트
        from services.problemgeneration_service import generate_vocabulary_options as gen_options
        
        result_items = []
        for item in request.items:
            try:
                # 선택지 생성 함수 호출
                options = gen_options(item.word, item.meaning)
                
                # 항목 생성
                result_item = create_vocabulary_item(item, options, request.userId, request.vocaId)
                result_items.append(result_item)
            except Exception as e:
                # 개별 항목 처리 중 오류 발생 시 오류 메시지 포함
                error_msg = f"'{item.word}' 단어의 선택지 생성 중 오류: {str(e)}"
                print(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)
        
        try:
            await save_vocabulary_items(result_items)
        except Exception as e:
            error_msg = f"항목 저장 중 오류 발생: {str(e)}"
            print(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        
        return {
            "status": "success",
            "data": prepare_response_items(result_items)
        }
    except HTTPException:
        # 이미 HTTPException인 경우 그대로 전달
        raise
    except Exception as e:
        import traceback
        error_msg = f"선택지 생성 중 오류 발생: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)

@vocabulary_router.get("", response_model=Dict[str, Any])
async def get_vocabulary_items(
    userId: Optional[str] = None,
    vocaId: Optional[str] = None,
    limit: int = 100,
    skip: int = 0
):
    """저장된 단어장 항목을 조회합니다."""
    try:
        filter_condition = create_filter_condition(userId, vocaId)
        items = await fetch_vocabulary_items(filter_condition, limit, skip)
        return {
            "status": "success",
            "count": len(items),
            "data": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"단어장 조회 중 오류 발생: {str(e)}")

