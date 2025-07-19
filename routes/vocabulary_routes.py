import sys
import os
import json
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, List, Optional
import datetime
from sqlalchemy.orm import Session

# 현재 디렉토리의 상위 디렉토리를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 상대 경로로 임포트
from model.EnglishModels import (
    VocabularyRequest, VocabularyGenerateRequest, VocabularyResponse
)
from model.database import get_db, VocabularyItem, Vocabulary

# utils.py 파일을 직접 import
import vocab_utils

vocabulary_router = APIRouter(
    prefix="/vocabulary", 
    tags=["Vocabulary"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)

# config 로딩을 함수 내부로 이동
def get_config():
    return vocab_utils.load_config()

def create_vocabulary_item(item, options, userId, vocaId, db: Session):
    """단어장 항목을 생성합니다."""
    options_json = json.dumps(options, ensure_ascii=False)
    db_item = VocabularyItem(
        word=item.word,
        meaning=item.meaning,
        options=options_json,
        userId=userId,
        vocaId=vocaId
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def prepare_response_items(items):
    """응답용 항목을 준비합니다."""
    result = []
    for item in items:
        options = json.loads(item.options) if item.options else []
        result.append({
            "word": item.word,
            "meaning": item.meaning,
            "options": options
        })
    return result

@vocabulary_router.post(
    "/generate", 
    response_model=VocabularyResponse,
    summary="단어장 생성",
    description="""
    ## 단어장 생성 API
    
    Ollama를 사용하여 학교 수준에 맞는 영어 단어장을 동적으로 생성합니다.
    
    ### 기능:
    - AI가 학교 수준에 맞는 영어 단어를 자동 생성
    - 단어와 한국어 의미 제공
    - 요청한 개수만큼 단어 생성
    - 실패 시 최대 3회 재시도
    
    ### 학교 수준별 난이도:
    - **초등학교**: 3-6학년 수준의 쉬운 단어
    - **중학교**: 1-3학년 수준의 중간 난이도 단어  
    - **고등학교**: 1-3학년 수준의 어려운 단어
    
    ### 응답 예시:
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
    """,
    responses={
        200: {
            "description": "단어장 생성 성공",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": [
                            {
                                "word": "apple",
                                "meaning": "사과",
                                "options": []
                            },
                            {
                                "word": "book",
                                "meaning": "책",
                                "options": []
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "단어장 생성 실패",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "단어장 생성 중 오류 발생: AI 모델 연결 실패"
                    }
                }
            }
        }
    }
)
async def generate_vocabulary(request: VocabularyRequest):
    """단어장 데이터를 동적으로 생성합니다."""
    try:
        # 요청 파라미터 추출
        count = request.count if request.count else 10
        school_level = request.school_level if request.school_level else "중등"
        topic = request.topic if request.topic else "일반"
        language = request.language if request.language else "영어"
        
        print(f"단어장 생성 요청: count={count}, school_level={school_level}, topic={topic}, language={language}")
        
        # 동적 단어장 생성 (주제와 언어 정보 포함)
        vocabulary_items = vocab_utils.generate_vocabulary(count, school_level, topic, language)
        
        # 응답 데이터 형식으로 변환
        formatted_items = []
        for item in vocabulary_items:
            formatted_item = {
                "word": item["word"],
                "meaning": item["meaning"],
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

@vocabulary_router.post(
    "/generate-options", 
    response_model=VocabularyResponse,
    summary="선택지 포함 단어장 생성",
    description="""
    ## 선택지 포함 단어장 생성 API
    
    단어와 의미를 받아서 객관식 선택지를 포함한 단어장 항목을 동적으로 생성하고 저장합니다.
    
    ### 기능:
    - 기존 단어에 대한 객관식 선택지 동적 생성
    - 생성된 항목을 MySQL에 저장
    - userId와 vocaId로 단어장 구분
    - 실패 시 최대 3회 재시도
    
    ### 필수 파라미터:
    - **userId**: 사용자 ID (필수)
    - **vocaId**: 단어장 ID (필수)
    - **items**: 단어 목록 (필수)
    
    ### 응답 예시:
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
    """,
    responses={
        200: {
            "description": "선택지 생성 및 저장 성공",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": [
                            {
                                "word": "apple",
                                "meaning": "사과",
                                "options": ["사과", "바나나", "오렌지", "포도"]
                            }
                        ]
                    }
                }
            }
        },
        400: {
            "description": "필수 파라미터 누락",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "userId와 vocaId는 필수 항목입니다."
                    }
                }
            }
        },
        500: {
            "description": "선택지 생성 실패",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "선택지 생성 중 오류 발생: AI 모델 연결 실패"
                    }
                }
            }
        }
    }
)
async def generate_vocabulary_options(
    request: VocabularyGenerateRequest,
    db: Session = Depends(get_db)
):
    """단어와 의미를 받아서 선택지를 포함한 단어장 항목을 동적으로 생성합니다."""
    try:
        # 필수 파라미터 검증
        if not request.userId or not request.vocaId:
            raise HTTPException(
                status_code=400, 
                detail="userId와 vocaId는 필수 항목입니다."
            )
        
        if not request.items or len(request.items) == 0:
            raise HTTPException(
                status_code=400, 
                detail="items는 비어있을 수 없습니다."
            )
        
        result_items = []
        
        # 각 단어에 대해 선택지 생성
        for item in request.items:
            try:
                # 동적 선택지 생성
                options = vocab_utils.generate_options(item.word, item.meaning)
                
                # 데이터베이스에 저장
                db_item = create_vocabulary_item(
                    item, options, request.userId, request.vocaId, db
                )
                
                # 응답 데이터에 추가
                result_items.append({
                    "word": item.word,
                    "meaning": item.meaning,
                    "options": options
                })
                
            except Exception as e:
                print(f"단어 '{item.word}'의 선택지 생성 실패: {str(e)}")
                # 선택지 생성 실패 시 에러를 그대로 전파
                raise HTTPException(
                    status_code=500, 
                    detail=f"단어 '{item.word}'의 선택지 생성 실패: {str(e)}"
                )
        
        return {
            "status": "success",
            "data": result_items
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"선택지 생성 중 오류 발생: {str(e)}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)

@vocabulary_router.get(
    "", 
    response_model=Dict[str, Any],
    summary="단어장 조회",
    description="""
    ## 단어장 조회 API
    
    저장된 단어장 항목을 조회합니다.
    
    ### 기능:
    - userId와 vocaId로 필터링 가능
    - 페이지네이션 지원 (limit, skip)
    - 저장된 모든 단어장 항목 조회
    
    ### 쿼리 파라미터:
    - **userId** (선택): 사용자 ID로 필터링
    - **vocaId** (선택): 단어장 ID로 필터링
    - **limit** (선택): 조회할 항목 수 (기본값: 100)
    - **skip** (선택): 건너뛸 항목 수 (기본값: 0)
    
    ### 응답 예시:
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
    """,
    responses={
        200: {
            "description": "단어장 조회 성공",
            "content": {
                "application/json": {
                    "example": {
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
                }
            }
        },
        500: {
            "description": "단어장 조회 실패",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "단어장 조회 중 오류 발생: 데이터베이스 연결 실패"
                    }
                }
            }
        }
    }
)
async def get_vocabulary_items(
    userId: Optional[str] = Query(None, description="사용자 ID로 필터링"),
    vocaId: Optional[str] = Query(None, description="단어장 ID로 필터링"),
    limit: int = Query(100, description="조회할 항목 수", ge=1, le=1000),
    skip: int = Query(0, description="건너뛸 항목 수", ge=0),
    db: Session = Depends(get_db)
):
    """저장된 단어장 항목을 조회합니다."""
    try:
        # 쿼리 조건 구성
        query = db.query(VocabularyItem)
        
        if userId:
            query = query.filter(VocabularyItem.userId == userId)
        
        if vocaId:
            query = query.filter(VocabularyItem.vocaId == vocaId)
        
        # 전체 개수 조회
        total_count = query.count()
        
        # 페이지네이션 적용
        items = query.offset(skip).limit(limit).all()
        
        # 응답 데이터 준비
        result_items = []
        for item in items:
            options = json.loads(item.options) if item.options else []
            result_items.append({
                "word": item.word,
                "meaning": item.meaning,
                "options": options,
                "userId": item.userId,
                "vocaId": item.vocaId,
                "createdAt": item.createdAt.isoformat() if item.createdAt else None
            })
        
        return {
            "status": "success",
            "count": total_count,
            "data": result_items
        }
        
    except Exception as e:
        error_msg = f"단어장 조회 중 오류 발생: {str(e)}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)

