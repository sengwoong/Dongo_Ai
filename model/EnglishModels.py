from pydantic import BaseModel
from typing import Optional, Dict, Any, List

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
    userId: Optional[str] = None
    vocaId: Optional[str] = None

class VocabularyItemRequest(BaseModel):
    word: str
    meaning: str

class VocabularyGenerateRequest(BaseModel):
    items: List[VocabularyItemRequest]
    userId: Optional[str] = None
    vocaId: Optional[str] = None

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

class ErrorResponse(BaseModel):
    status: str
    message: str 