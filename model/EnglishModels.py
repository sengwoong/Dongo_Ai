from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class WordRequest(BaseModel):
    word: str = Field(..., description="영어 단어", example="apple")
    meaning: str = Field(..., description="한국어 의미", example="사과")
    vocaId: int = Field(..., description="단어장 ID", example=1)
    schoolLevel: Optional[str] = Field("중등", description="학교 수준", example="중등")

class RouletteRequest(BaseModel):
    word: str = Field(..., description="영어 단어", example="apple")
    count: Optional[int] = Field(8, description="생성할 선택지 개수", example=8)

class VocabularyRequest(BaseModel):
    count: Optional[int] = Field(10, description="생성할 단어 개수 (1-50)", example=10, ge=1, le=50)
    school_level: Optional[str] = Field("중등", description="학교 수준 (초등학교/중학교/고등학교)", example="중등")
    topic: Optional[str] = Field("일반", description="단어장 주제", example="음식")
    language: Optional[str] = Field("영어", description="언어", example="영어")
    userId: Optional[str] = Field(None, description="사용자 ID", example="user123")
    vocaId: Optional[str] = Field(None, description="단어장 ID", example="voca456")

    class Config:
        json_schema_extra = {
            "example": {
                "count": 10,
                "school_level": "중등",
                "topic": "음식",
                "language": "영어",
                "userId": "user123",
                "vocaId": "voca456"
            }
        }

class VocabularyItemRequest(BaseModel):
    word: str = Field(..., description="영어 단어", example="apple")
    meaning: str = Field(..., description="한국어 의미", example="사과")

    class Config:
        json_schema_extra = {
            "example": {
                "word": "apple",
                "meaning": "사과"
            }
        }

class VocabularyGenerateRequest(BaseModel):
    items: List[VocabularyItemRequest] = Field(..., description="단어 목록", min_items=1)
    userId: Optional[str] = Field(None, description="사용자 ID", example="user123")
    vocaId: Optional[str] = Field(None, description="단어장 ID", example="voca456")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {"word": "apple", "meaning": "사과"},
                    {"word": "book", "meaning": "책"}
                ],
                "userId": "user123",
                "vocaId": "voca456"
            }
        }

class WordResponse(BaseModel):
    status: str = Field(..., description="응답 상태", example="success")
    data: Dict[str, Any] = Field(..., description="응답 데이터")

class RouletteItem(BaseModel):
    id: int = Field(..., description="선택지 ID", example=1)
    name: str = Field(..., description="선택지 이름", example="사과")
    color: str = Field(..., description="선택지 색상", example="#FF0000")
    percentage: int = Field(..., description="선택지 확률 (%)", example=25)

class RouletteResponse(BaseModel):
    status: str = Field(..., description="응답 상태", example="success")
    data: List[RouletteItem] = Field(..., description="선택지 목록")

class VocabularyItem(BaseModel):
    word: str = Field(..., description="영어 단어", example="apple")
    meaning: str = Field(..., description="한국어 의미", example="사과")
    options: List[str] = Field(..., description="객관식 선택지 목록", example=["사과", "바나나", "오렌지", "포도"])

    class Config:
        json_schema_extra = {
            "example": {
                "word": "apple",
                "meaning": "사과",
                "options": ["사과", "바나나", "오렌지", "포도"]
            }
        }

class VocabularyResponse(BaseModel):
    status: str = Field(..., description="응답 상태", example="success")
    data: List[VocabularyItem] = Field(..., description="단어장 항목 목록")

    class Config:
        json_schema_extra = {
            "example": {
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
                        "options": ["책", "펜", "지우개", "가방"]
                    }
                ]
            }
        }

class ErrorResponse(BaseModel):
    status: str = Field(..., description="에러 상태", example="error")
    message: str = Field(..., description="에러 메시지", example="단어장 생성 중 오류가 발생했습니다.")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "message": "단어장 생성 중 오류가 발생했습니다."
            }
        } 