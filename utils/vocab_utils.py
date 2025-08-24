import yaml
import requests
import json
import random
import re
import time
import logging
import os
from typing import Tuple, List, Dict
from dotenv import load_dotenv

# 로깅 설정 (모듈 전용 로거)
_log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
_log_dir = os.path.abspath(_log_dir)
os.makedirs(_log_dir, exist_ok=True)

logger = logging.getLogger("vocab_utils")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _file_handler = logging.FileHandler(os.path.join(_log_dir, 'vocab_utils.log'), encoding='utf-8')
    _stream_handler = logging.StreamHandler()
    _formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    _file_handler.setFormatter(_formatter)
    _stream_handler.setFormatter(_formatter)
    logger.addHandler(_file_handler)
    logger.addHandler(_stream_handler)
logger.propagate = False

# .env 로드 (GPT_KEY 등)
load_dotenv()

# =============================
# Generation & configuration
# =============================
# 설정 캐싱을 위한 전역 변수
_config_cache = None
_config_cache_time = None

def load_config():
    """YAML 설정 파일을 로드합니다. (캐싱 적용)"""
    global _config_cache, _config_cache_time
    
    # 캐시가 5분 이내면 캐시된 설정 반환
    if _config_cache and _config_cache_time:
        if time.time() - _config_cache_time < 300:  # 5분
            return _config_cache
    
    try:
        with open("EnglishCommand.yaml", "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
            _config_cache = config
            _config_cache_time = time.time()
            return config
    except Exception as e:
        raise Exception(f"YAML 파일을 로드하는 중 오류가 발생했습니다: {e}")

def generate_with_gpt(prompt: str, config: Dict) -> str:
    """모델 제공자에 따라 텍스트를 생성합니다. (openai 또는 ollama)"""
    provider = (config.get("model", {}).get("provider") or "ollama").lower()
    model_name = config["model"]["name"]
    temperature = config["model"].get("temperature", 0.7)
    top_p = config["model"].get("top_p", 0.9)
    max_tokens = config["model"].get("max_tokens", 500)

    logger.info("🚀 모델 호출 시작")
    logger.info(f"🔧 제공자: {provider}")
    logger.info(f"🧠 모델: {model_name}")
    logger.info(f"🌡️ 온도: {temperature}")

    try:
        if provider == "openai":
            api_base = config["model"].get("api_base", "https://api.openai.com/v1")
            api_key = os.getenv("GPT_KEY")
            if not api_key:
                raise Exception("환경변수 GPT_KEY가 설정되어 있지 않습니다.")

            url = f"{api_base.rstrip('/')}/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
            }

            logger.debug(f"🌐 URL: {url}")
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            logger.info(f"📊 응답 상태 코드: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            if not content:
                raise Exception("빈 응답을 받았습니다.")
            logger.info(f"📄 응답 길이: {len(content)} 문자")
            logger.info("✅ API 호출 성공")
            return content

    except requests.exceptions.ConnectionError:
        error_msg = "모델 서버에 연결할 수 없습니다."
        logger.error(f"🔌 연결 오류: {error_msg}")
        raise Exception(error_msg)
    except requests.exceptions.Timeout:
        error_msg = "요청 시간 초과."
        logger.error(f"⏰ 시간 초과: {error_msg}")
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"모델 호출 중 오류 발생: {str(e)}"
        logger.error(f"❌ 일반 오류: {error_msg}")
        raise Exception(error_msg)

 

# =============================
# Parsing & regex helpers
# =============================
def parse_vocabulary_options(text: str) -> List[str]:
    """생성된 텍스트에서 선택지를 동적으로 파싱합니다."""
    options = []
    
    # 먼저 전체 텍스트에서 한글 단어들을 추출
    # 괄호, 영어, 하이픈 등을 모두 제거하고 한글만 남김
    cleaned_text = re.sub(r'\([^)]*\)', '', text)  # 괄호 내용 제거
    cleaned_text = re.sub(r'[a-zA-Z\-]', '', cleaned_text)  # 영어와 하이픈 제거
    cleaned_text = re.sub(r'[^가-힣,\s]', '', cleaned_text)  # 한글, 쉼표, 공백만 남김
    
    # 쉼표로 분리하여 단어 추출
    words = [word.strip() for word in cleaned_text.split(',') if word.strip()]
    
    for word in words:
        # clean_option 함수로 정제
        cleaned_word = clean_option(word)
        if is_valid_option(cleaned_word) and cleaned_word not in options:
            options.append(cleaned_word)
    
    return options[:4]  # 최대 4개까지만 반환

def clean_option(option: str) -> str:
    """선택지 텍스트를 동적으로 정제합니다."""
    if not option:
        return ""
    
    opt = option.strip()
    
    # 번호, 기호 제거
    opt = re.sub(r'^[0-9*\-•]+\.?\s*', '', opt)
    
    # 괄호 내용 제거
    opt = re.sub(r'\([^)]*\)', '', opt)
    
    # 하이픈 뒤 내용 제거
    opt = re.sub(r'\s*-.*$', '', opt)
    
    # 영어 단어 제거 (3글자 이상)
    opt = re.sub(r'[a-zA-Z]{3,}', '', opt)
    
    # 따옴표 제거
    opt = re.sub(r'^["\']|["\']$', '', opt)
    
    # 공백 정리
    opt = re.sub(r'\s+', ' ', opt).strip()
    
    return opt

def is_valid_option(option: str) -> bool:
    """선택지가 유효한지 동적으로 검사합니다."""
    if not option:
        return False
    
    # 길이 검사
    if len(option) < 1 or len(option) > 20:
        return False
    
    # 한글이나 영어가 포함되어야 함
    if not re.search(r'[가-힣a-zA-Z]', option):
        return False
    
    # 특수문자만으로 구성된 경우 제외
    if re.match(r'^[^\w\s가-힣]+$', option):
        return False
    
    return True

def clean_meaning(meaning: str) -> str:
    """의미에서 발음 표기와 불필요한 내용을 동적으로 제거합니다."""
    if not meaning:
        return ""
    
    # 괄호 내용 제거
    cleaned = re.sub(r'\([^)]*\)', '', meaning)
    
    # 대괄호 내용 제거
    cleaned = re.sub(r'\[[^\]]*\]', '', cleaned)
    
    # 따옴표 제거
    cleaned = re.sub(r'["\']', '', cleaned)
    
    # 공백 정리
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned

def ensure_correct_answer_first(options: List[str], correct_answer: str) -> List[str]:
    """정답이 첫 번째 위치에 오도록 동적으로 보장합니다."""
    if not options:
        raise ValueError("선택지 목록이 비어 있습니다.")
    
    if not correct_answer:
        raise ValueError("정답이 비어 있습니다.")
    
    # 정답 정제
    cleaned_correct = clean_meaning(correct_answer)
    
    # 중복 제거
    unique_options = []
    for opt in options:
        cleaned_opt = clean_option(opt)
        if cleaned_opt and cleaned_opt not in unique_options:
            unique_options.append(cleaned_opt)
    
    # 정답이 이미 있는지 확인
    if cleaned_correct in unique_options:
        unique_options.remove(cleaned_correct)
    
    # 정답을 첫 번째로 추가
    final_options = [cleaned_correct] + unique_options
    
    # 4개 미만이면 한글 한 글자씩 랜덤으로 채움
    if len(final_options) < 4:
        # 한글 자음과 모음 조합으로 랜덤 한 글자 생성
        consonants = ['ㄱ', 'ㄴ', 'ㄷ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅅ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
        vowels = ['ㅏ', 'ㅑ', 'ㅓ', 'ㅕ', 'ㅗ', 'ㅛ', 'ㅜ', 'ㅠ', 'ㅡ', 'ㅣ']
        
        while len(final_options) < 4:
            # 랜덤하게 자음+모음 조합으로 한 글자 생성
            random_char = random.choice(consonants) + random.choice(vowels)
            if random_char not in final_options:
                final_options.append(random_char)
    
    return final_options[:4]

def parse_vocabulary_response(text: str) -> List[Dict[str, str]]:
    """생성된 텍스트에서 단어장 데이터를 동적으로 파싱합니다."""
    vocabulary_data = []
    
    # 다양한 형식의 파싱 시도
    patterns = [
        # 형식 1: "단어: apple\n의미: 사과"
        r'(?:단어|word):\s*["\']?([^"\'\n]+)["\']?\s*(?:의미|meaning):\s*([^\n]+)',
        # 형식 2: "1. Word: apple\n   Meaning: 사과"
        r'\d+\.\s*(?:단어|word):\s*["\']?([^"\'\n]+)["\']?\s*(?:의미|meaning):\s*([^\n]+)',
        # 형식 3: "-단어: apple\n-의미: 사과"
        r'[-•]\s*(?:단어|word):\s*["\']?([^"\'\n]+)["\']?\s*(?:의미|meaning):\s*([^\n]+)',
        # 형식 4: "apple: 사과"
        r'([a-zA-Z]+):\s*([^\n]+)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        if matches:
            for word, meaning in matches:
                cleaned_word = word.strip()
                cleaned_meaning = clean_meaning(meaning.strip())
                
                if cleaned_word and cleaned_meaning:
                    vocabulary_data.append({
                        "word": cleaned_word,
                        "meaning": cleaned_meaning
                    })
            break
    
    return vocabulary_data










