import yaml
import requests
import json
import random
import re
from typing import Tuple, List, Dict, Any
from datetime import datetime

def load_config():
    """YAML 설정 파일을 로드합니다."""
    try:
        with open("EnglishCommand.yaml", "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except Exception as e:
        raise Exception(f"YAML 파일을 로드하는 중 오류가 발생했습니다: {e}")

def generate_with_ollama(prompt: str, config: Dict) -> str:
    """Ollama API를 사용하여 텍스트를 생성합니다."""
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
        
        full_response = ""
        for line in response.text.strip().split('\n'):
            if line:
                data = json.loads(line)
                full_response += data.get("response", "")
                if data.get("done", False):
                    break
        
        return full_response
    except requests.exceptions.ConnectionError:
        raise Exception("Ollama 서버에 연결할 수 없습니다.")
    except Exception as e:
        raise Exception(f"Ollama API 호출 중 오류 발생: {str(e)}")

def generate_mock_id() -> int:
    """모의 ID를 생성합니다."""
    return random.randint(1000, 9999)

def get_difficulty_settings(school_level: str) -> Tuple[str, str]:
    """학교 수준에 따른 난이도 설정을 반환합니다."""
    settings = {
        "초등": ("쉬운", "1-6학년"),
        "중등": ("중간", "7-9학년"),
        "고등": ("어려운", "10-12학년")
    }
    return settings.get(school_level, ("중간", "전체"))

def parse_vocabulary_options(text: str) -> List[str]:
    """생성된 텍스트에서 선택지를 파싱합니다."""
    options = []
    cleaned_text = re.sub(r'.*생성된 텍스트:.*\n?', '', text)
    
    if "," in cleaned_text:
        first_line = cleaned_text.split('\n')[0].strip()
        if ":" in first_line:
            first_line = first_line.split(":", 1)[1].strip()
        
        raw_options = first_line.split(',')
        for opt in raw_options:
            opt = clean_option(opt)
            if is_valid_option(opt):
                options.append(opt)
    
    return options

def clean_option(option: str) -> str:
    """선택지 텍스트를 정제합니다."""
    opt = option.strip()
    opt = re.sub(r'^[0-9*\-•]+\.?\s*', '', opt)
    opt = re.sub(r'\([^)]*\)', '', opt)
    opt = re.sub(r'\s*-.*$', '', opt)
    opt = re.sub(r'[a-zA-Z]{3,}', '', opt)
    return opt.strip()

def is_valid_option(option: str) -> bool:
    """선택지가 유효한지 검사합니다."""
    return bool(option and len(option) < 20)

def clean_meaning(meaning: str) -> str:
    """의미에서 발음 표기 제거"""
    return re.sub(r'\(.*?\)', '', meaning).strip()

def ensure_correct_answer_first(options: List[str], correct_answer: str) -> List[str]:
    """정답이 첫 번째 위치에 오도록 보장"""
    if not options:
        raise ValueError("선택지 목록이 비어 있습니다.")
    
    if correct_answer in options:
        options.remove(correct_answer)
    else:
        if len(options) >= 4:
            options.pop()
    
    options.insert(0, correct_answer)
    
    if len(options) < 4:
        from config import DEFAULT_OPTIONS
        category = guess_category_from_config(correct_answer, DEFAULT_OPTIONS)
        if category in DEFAULT_OPTIONS:
            for opt in DEFAULT_OPTIONS[category]:
                if opt != correct_answer and opt not in options and len(options) < 4:
                    options.append(opt)
    
    return options[:4]

def get_default_options_from_config(meaning: str, default_options: Dict[str, List[str]]) -> List[str]:
    category = guess_category_from_config(meaning, default_options)
    if category in default_options:
        options = [meaning]
        for opt in default_options[category]:
            if opt != meaning and len(options) < 4:
                options.append(opt)
    else:
        options = [meaning]
        for cat, opts in default_options.items():
            for opt in opts:
                if opt != meaning and opt not in options and len(options) < 4:
                    options.append(opt)
    
    return options

def guess_category_from_config(word: str, default_options: Dict[str, List[str]]) -> str:
    for category, words in default_options.items():
        if word in words:
            return category
    return list(default_options.keys())[0] if default_options else "기타"

def generate_default_options(meaning: str) -> List[str]:
    from config import DEFAULT_OPTIONS
    category = guess_category(meaning)
    if category in DEFAULT_OPTIONS:
        options = [meaning]
        for opt in DEFAULT_OPTIONS[category]:
            if opt != meaning and len(options) < 4:
                options.append(opt)
    else:
        options = [meaning, "포도", "바나나", "딸기"]
    
    while len(options) < 4:
        fallback = ["학교", "책", "펜", "노트"]
        for opt in fallback:
            if opt not in options and len(options) < 4:
                options.append(opt)
    
    return options

def guess_category(word: str) -> str:
    fruit_words = ["사과", "배", "포도", "오렌지", "바나나", "딸기", "키위"]
    vegetable_words = ["당근", "양파", "감자", "배추", "시금치", "오이"]
    animal_words = ["개", "고양이", "말", "소", "돼지", "토끼", "사자"]
    
    if word in fruit_words:
        return "과일"
    elif word in vegetable_words:
        return "채소"
    elif word in animal_words:
        return "동물"
    else:
        return "기타"

def generate_default_options_with_exact_meaning(meaning: str) -> List[str]:
    meaning_clean = meaning.split('(')[0].strip()
    if meaning_clean in ["중등", "중학생"]:
        return [meaning, "초등", "고등", "대학생"]
    elif meaning_clean in ["초등", "초등학생"]:
        return [meaning, "중등", "고등", "유치원생"]
    elif meaning_clean in ["고등", "고등학생"]:
        return [meaning, "중등", "대학생", "초등"]
    elif "학생" in meaning_clean:
        return [meaning, "선생님", "교수", "학부모"]
    elif "도시" in meaning_clean:
        return [meaning, "시골", "마을", "농촌"]
    
    common_words = ["학교", "공부", "시험", "숙제", "책", "연필", "노트", "교실", "선생님", "학생", "친구", "가족", "집", "도시", "나라", "세계"]
    options = [meaning]
    random.shuffle(common_words)
    
    for word in common_words:
        if len(options) >= 4:
            break
        if word != meaning_clean and word not in options:
            options.append(word)
    
    if len(options) < 4:
        remaining = 4 - len(options)
        additional = [f"다른 {meaning_clean}", f"새로운 {meaning_clean}", f"특별한 {meaning_clean}", f"중요한 {meaning_clean}"]
        
        for i in range(min(remaining, len(additional))):
            options.append(additional[i])
    
    return options

def ensure_four_options_with_exact_meaning(options_list: List[str], meaning: str) -> List[str]:
    if options_list[0] != meaning:
        if meaning in options_list:
            options_list.remove(meaning)
        options_list.insert(0, meaning)
    
    if len(options_list) < 4:
        meaning_clean = meaning.split('(')[0].strip()
        additional_options = [f"다른 {meaning_clean}", f"새로운 {meaning_clean}", f"특별한 {meaning_clean}", f"중요한 {meaning_clean}"]
        
        for opt in additional_options:
            if len(options_list) >= 4:
                break
            if opt not in options_list:
                options_list.append(opt)
    
    return options_list[:4] 