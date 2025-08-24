import os
import sys
import json
import uuid
from typing import Optional, List, Dict, Tuple
from sqlalchemy.orm import Session

# 현재 디렉토리의 상위 디렉토리를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import VocabularyItem, Vocabulary


def create_vocabulary_item(item, options, userId, vocaId, db: Session):
    """단어장 항목을 생성합니다."""
    # 사전 조건: 상위 vocabularies에 해당 vocaId가 존재해야 함 (FK 제약)
    parent = db.query(Vocabulary).filter(Vocabulary.vocaId == vocaId).first()
    if not parent:
        raise ValueError(f"존재하지 않는 vocaId입니다: {vocaId}. 먼저 vocabularies에 생성해야 합니다.")
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


 


def create_vocabulary_items(
    items: list,
    userId: str,
    vocaId: Optional[str],
    db: Session,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    schoolLevel: Optional[str] = None,
) -> Tuple[str, int]:
    """여러 단어 항목을 저장합니다. 반환: (vocaId, 저장 개수)"""
    parent = ensure_vocabulary_exists(
        userId, vocaId, db, title=title, description=description, schoolLevel=schoolLevel
    )
    used_voca_id = parent.vocaId
    saved = 0
    for it in items:
        word = it.get("word") if isinstance(it, dict) else getattr(it, "word", None)
        meaning = it.get("meaning") if isinstance(it, dict) else getattr(it, "meaning", None)
        if not word or not meaning:
            continue
        options_json = json.dumps([], ensure_ascii=False)
        entity = VocabularyItem(
            word=word,
            meaning=meaning,
            options=options_json,
            userId=userId,
            vocaId=used_voca_id,
        )
        db.add(entity)
        saved += 1
    if saved:
        db.commit()
    return used_voca_id, saved


def create_vocabulary_item_single(
    userId: str,
    vocaId: Optional[str],
    word: str,
    meaning: str,
    db: Session,
    *,
    options: Optional[List[str]] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    schoolLevel: Optional[str] = None,
) -> VocabularyItem:
    parent = ensure_vocabulary_exists(
        userId, vocaId, db, title=title, description=description, schoolLevel=schoolLevel
    )
    options_json = json.dumps(options or [], ensure_ascii=False)
    entity = VocabularyItem(
        word=word,
        meaning=meaning,
        options=options_json,
        userId=userId,
        vocaId=parent.vocaId,
    )
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


def update_vocabulary_item(
    db: Session,
    item_id: int,
    *,
    word: Optional[str] = None,
    meaning: Optional[str] = None,
    options: Optional[List[str]] = None,
) -> Optional[VocabularyItem]:
    item = db.query(VocabularyItem).filter(VocabularyItem.id == item_id).first()
    if not item:
        return None
    if word is not None:
        item.word = word
    if meaning is not None:
        item.meaning = meaning
    if options is not None:
        item.options = json.dumps(options, ensure_ascii=False)
    db.commit()
    db.refresh(item)
    return item


def delete_vocabulary_item(db: Session, item_id: int) -> bool:
    item = db.query(VocabularyItem).filter(VocabularyItem.id == item_id).first()
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True




def list_vocabulary_items(
    db: Session,
    userId: Optional[str] = None,
    vocaId: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
) -> Tuple[int, List[Dict]]:
    """필터 및 페이지네이션을 적용한 단어장 항목 리스트와 총 개수를 반환합니다."""
    query = db.query(VocabularyItem)
    if userId:
        query = query.filter(VocabularyItem.userId == userId)
    if vocaId:
        query = query.filter(VocabularyItem.vocaId == vocaId)
    total_count = query.count()
    items = query.offset(skip).limit(limit).all()
    data = [_serialize_vocabulary_item(it) for it in items]
    return total_count, data


 


def get_vocabulary_item_by_word(
    db: Session,
    word: str,
    userId: Optional[str] = None,
    vocaId: Optional[str] = None,
) -> Optional[Dict]:
    query = db.query(VocabularyItem).filter(VocabularyItem.word == word)
    if userId:
        query = query.filter(VocabularyItem.userId == userId)
    if vocaId:
        query = query.filter(VocabularyItem.vocaId == vocaId)
    item = query.first()
    return _serialize_vocabulary_item(item) if item else None



def ensure_vocabulary_exists(
    userId: str,
    vocaId: Optional[str],
    db: Session,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    schoolLevel: Optional[str] = None,
) -> Vocabulary:
    """부모 단어장(Vocabulary)을 보장합니다. vocaId 없으면 자동 생성합니다.
    title가 NULL이면 DB 제약에 걸리므로 기본값을 채웁니다.
    """
    if vocaId:
        parent = db.query(Vocabulary).filter(
            Vocabulary.userId == userId, Vocabulary.vocaId == vocaId
        ).first()
        if parent:
            return parent
    # 새 vocaId 생성 (voca-xxxxxxxx)
    new_voca_id = vocaId or f"voca-{uuid.uuid4().hex[:8]}"
    parent = Vocabulary(
        userId=userId,
        vocaId=new_voca_id,
        title=title or "단어장",
        description=description or "",
        schoolLevel=schoolLevel or "중등",
    )
    db.add(parent)
    db.commit()
    db.refresh(parent)
    return parent


def _serialize_vocabulary_item(item: VocabularyItem) -> Dict:
    options = json.loads(item.options) if item.options else []
    return {
        "word": item.word,
        "meaning": item.meaning,
        "options": options,
        "userId": item.userId,
        "vocaId": item.vocaId,
        "createdAt": item.createdAt.isoformat() if getattr(item, "createdAt", None) else None,
    }