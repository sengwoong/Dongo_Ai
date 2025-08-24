import sys
import os
import json
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, List, Optional
import datetime
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.EnglishModels import (
    VocabularyRequest, VocabularyGenerateRequest, VocabularyResponse
)
from models.database import get_db, VocabularyItem, Vocabulary

from services.problemgeneration import (
    generate_vocabulary as ai_generate_vocabulary,
    generate_options as ai_generate_options,
)
from services.vocabulary import (
    create_vocabulary_item,
    list_vocabulary_items,
    get_vocabulary_item_by_word,
    create_vocabulary_items,
    create_vocabulary_item_single,
    update_vocabulary_item,
    delete_vocabulary_item,
)

vocabulary_router = APIRouter(
    prefix="/vocabulary", 
    tags=["Vocabulary"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)



@vocabulary_router.post("/generate")
async def generate_vocabulary(request: VocabularyRequest, db: Session = Depends(get_db)):
    try:
        # 요청 파라미터 추출
        count = request.count if request.count else 10
        school_level = request.school_level if request.school_level else "중등"
        topic = request.topic if request.topic else "일반"
        language = request.language if request.language else "영어"
        
        print(f"단어장 생성 요청: count={count}, school_level={school_level}, topic={topic}, language={language}")
        
        # 동적 단어장 생성 (주제와 언어 정보 포함)
        vocabulary_items = ai_generate_vocabulary(count, school_level, topic, language)

        # 저장: userId가 있으면 vocaId 자동 생성/보장, 없으면 저장 생략
        used_voca_id = None
        if request.userId:
            used_voca_id, created = create_vocabulary_items(
                vocabulary_items,
                request.userId,
                getattr(request, 'vocaId', None),
                db,
                title=f"{topic} 단어장",
                description=f"{school_level}용 {topic} 단어장",
                schoolLevel=school_level,
            )
        
        # 응답 데이터 형식으로 변환
        formatted_items = []
        for item in vocabulary_items:
            formatted_item = {
                "word": item["word"],
                "meaning": item["meaning"],
                "options": []  # 이 시점에서는 선택지 없음
            }
            formatted_items.append(formatted_item)
        
        payload = {"status": "success", "data": formatted_items}
        if used_voca_id:
            payload["vocaId"] = used_voca_id
        return payload
    except Exception as e:
        error_msg = f"단어장 생성 중 오류 발생: {str(e)}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)

@vocabulary_router.post("/generate-options")
async def generate_vocabulary_options(
    request: VocabularyGenerateRequest,
    db: Session = Depends(get_db)
):
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
                options = ai_generate_options(item.word, item.meaning)
                
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

@vocabulary_router.get("")
async def get_vocabulary_items(
    userId: Optional[str] = Query(None, description="사용자 ID로 필터링"),
    vocaId: Optional[str] = Query(None, description="단어장 ID로 필터링"),
    limit: int = Query(100, description="조회할 항목 수", ge=1, le=1000),
    skip: int = Query(0, description="건너뛸 항목 수", ge=0),
    db: Session = Depends(get_db)
):
    try:
        total_count, result_items = list_vocabulary_items(
            db=db, userId=userId, vocaId=vocaId, limit=limit, skip=skip
        )
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


@vocabulary_router.post("")
async def create_item(
    userId: str = Query(...),
    word: str = Query(...),
    meaning: str = Query(...),
    vocaId: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    schoolLevel: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        entity = create_vocabulary_item_single(
            userId,
            vocaId,
            word,
            meaning,
            db,
            title=title,
            description=description,
            schoolLevel=schoolLevel,
        )
        return {"status": "success", "data": {"id": entity.id}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@vocabulary_router.get("/by-word")
async def get_vocabulary_item_word(
    word: str = Query(..., description="영어 단어"),
    userId: Optional[str] = Query(None),
    vocaId: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        item = get_vocabulary_item_by_word(db, word, userId=userId, vocaId=vocaId)
        if not item:
            raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
        return {"status": "success", "data": item}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@vocabulary_router.put("")
async def update_item(
    id: int = Query(...),
    word: Optional[str] = Query(None),
    meaning: Optional[str] = Query(None),
    options: Optional[str] = Query(None, description="JSON array string"),
    db: Session = Depends(get_db)
):
    try:
        options_list = json.loads(options) if options else None
        entity = update_vocabulary_item(db, id, word=word, meaning=meaning, options=options_list)
        if not entity:
            raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@vocabulary_router.delete("")
async def delete_item(
    id: int = Query(...),
    db: Session = Depends(get_db)
):
    try:
        ok = delete_vocabulary_item(db, id)
        if not ok:
            raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@vocabulary_router.post("/fill-missing-options")
async def fill_missing_options(
    userId: Optional[str] = Query(None),
    vocaId: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    try:
        # 대상 조회 (필터 적용)
        query = db.query(VocabularyItem)
        if userId:
            query = query.filter(VocabularyItem.userId == userId)
        if vocaId:
            query = query.filter(VocabularyItem.vocaId == vocaId)

        candidates = query.all()
        to_update = []
        for item in candidates:
            try:
                parsed = json.loads(item.options) if item.options else []
            except Exception:
                parsed = []
            if not parsed:
                to_update.append(item)

        updated = 0
        processed_items = []
        for item in to_update[:limit]:
            try:
                options = ai_generate_options(item.word, item.meaning)
                entity = update_vocabulary_item(db, item.id, options=options)
                if entity:
                    updated += 1
                    processed_items.append({
                        "id": entity.id,
                        "word": entity.word,
                        "meaning": entity.meaning,
                        "options": options,
                    })
            except Exception as e:
                # 개별 항목 실패는 무시하고 계속 진행
                continue

        return {
            "status": "success",
            "updated": updated,
            "total_candidates": len(to_update),
            "data": processed_items,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

