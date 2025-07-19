import yaml
import requests
import json
import random
import re
import time
import logging
from typing import Tuple, List, Dict, Any, Optional
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vocab_utils.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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

def generate_with_ollama(prompt: str, config: Dict) -> str:
    """Ollama API를 사용하여 텍스트를 생성합니다."""
    logger.info("🚀 Ollama API 호출 시작")
    logger.info(f"🔧 모델: {config['model']['name']}")
    logger.info(f"🌡️ 온도: {config['model']['temperature']}")
    
    try:
        logger.info("📡 API 요청 전송")
        
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": config["model"]["name"],
            "prompt": prompt,
            "temperature": config["model"]["temperature"],
            "top_p": config["model"]["top_p"],
            "max_tokens": config["model"]["max_tokens"]
        }
        
        logger.debug(f"🌐 URL: {url}")
        logger.debug(f"📦 Payload 크기: {len(str(payload))} bytes")
        
        response = requests.post(url, json=payload, timeout=30)
        logger.info(f"📊 응답 상태 코드: {response.status_code}")
        
        response.raise_for_status()
        
        full_response = ""
        for line in response.text.strip().split('\n'):
            if line:
                data = json.loads(line)
                full_response += data.get("response", "")
                if data.get("done", False):
                    break
        
        logger.info(f"📄 응답 길이: {len(full_response)} 문자")
        
        if full_response.strip():
            logger.info("✅ API 호출 성공")
            return full_response
        else:
            raise Exception("빈 응답을 받았습니다.")
            
    except requests.exceptions.ConnectionError as e:
        error_msg = "Ollama 서버에 연결할 수 없습니다."
        logger.error(f"🔌 연결 오류: {error_msg}")
        raise Exception(error_msg)
    except requests.exceptions.Timeout as e:
        error_msg = "요청 시간 초과."
        logger.error(f"⏰ 시간 초과: {error_msg}")
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Ollama API 호출 중 오류 발생: {str(e)}"
        logger.error(f"❌ 일반 오류: {error_msg}")
        raise Exception(error_msg)

def generate_mock_id() -> int:
    """모의 ID를 생성합니다."""
    return random.randint(1000, 9999)

def get_difficulty_settings(school_level: str) -> Tuple[str, str]:
    """학교 수준에 따른 난이도 설정을 동적으로 반환합니다."""
    settings = {
        "초등": ("쉬운", "1-6학년"),
        "중등": ("중간", "7-9학년"),
        "고등": ("어려운", "10-12학년")
    }
    return settings.get(school_level, ("중간", "전체"))

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

def generate_vocabulary(count: int, school_level: str, topic: str = "일반", language: str = "영어") -> List[Dict[str, str]]:
    """단어장을 동적으로 생성합니다."""
    config = load_config()
    
    # 명령어 설정 찾기
    cmd_config = None
    for cmd in config.get("commands", []):
        if cmd.get("name") == "generate_vocabulary":
            cmd_config = cmd
            break
    
    if not cmd_config:
        raise ValueError("generate_vocabulary 명령어를 찾을 수 없습니다.")
    
    logger.info(f"🎯 단어장 생성 시작: count={count}, school_level={school_level}, topic={topic}, language={language}")
    
    # 프롬프트 생성 (주제와 언어 정보 포함)
    prompt = cmd_config["prompt_template"].format(
        count=count,
        school_level=school_level,
        topic=topic,
        language=language
    )
    
    try:
        response = generate_with_ollama(prompt, config)
        vocabulary_data = parse_vocabulary_response(response)
        
        if len(vocabulary_data) >= count:
            return vocabulary_data[:count]
        else:
            raise ValueError(f"요청한 개수({count})보다 적은 단어({len(vocabulary_data)})가 생성되었습니다.")
            
    except Exception as e:
        raise e

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

def generate_options(word: str, meaning: str) -> List[str]:
    """단어에 대한 선택지를 동적으로 생성합니다."""
    logger.info(f"🔍 선택지 생성 시작: 단어='{word}', 의미='{meaning}'")
    
    config = load_config()
    logger.info(f"📋 설정 로드 완료: 모델={config['model']['name']}")
    
    options = [meaning]  # 정답을 첫 번째로 추가
    max_attempts = 5  # 최대 시도 횟수
    
    try:
        # 3번 더 호출해서 오답 3개 생성 (총 4개)
        for i in range(3):
            logger.info(f"🔄 API 호출 {i+1}/3")
            
            # 프롬프트 생성 (한 개만 생성하도록 수정)
            prompt = f"""다음 영어 단어의 의미와 같은 카테고리에 속하는 다른 한국어 단어를 1개만 생성해주세요.

단어: {word}
의미: {meaning}

생성 규칙:
1. 정답 '{meaning}'과 같은 카테고리의 단어여야 합니다.
2. 정답과 중복되지 않아야 합니다.
3. 한국어로만 작성하세요.
4. 1개만 생성하세요.
5. 번호, 기호, 영어, 발음 표기 없이 단어만 작성하세요.

예시: apple(사과) → 바나나"""
            
            response = generate_with_ollama(prompt, config)
            logger.info(f"🤖 AI 응답 {i+1}: {response[:100]}...")
            
            # 응답에서 한글 단어만 추출
            cleaned_response = re.sub(r'\([^)]*\)', '', response)  # 괄호 제거
            cleaned_response = re.sub(r'[a-zA-Z\-]', '', cleaned_response)  # 영어/하이픈 제거
            cleaned_response = re.sub(r'[^가-힣]', '', cleaned_response)  # 한글만 남김
            
            if cleaned_response and cleaned_response not in options:
                options.append(cleaned_response)
                logger.info(f"✅ 추가된 선택지: {cleaned_response}")
            else:
                logger.warning(f"⚠️ 중복 또는 빈 응답, 재시도")
        
        # 품질 테스트 및 재생성
        logger.info(f"🔍 품질 테스트 시작")
        final_options = quality_check_and_regenerate(word, meaning, options, config, max_attempts)
        
        logger.info(f"📊 최종 선택지: {final_options}")
        return final_options[:4]  # 최대 4개까지만 반환
        
    except Exception as e:
        logger.error(f"❌ 선택지 생성 실패: {str(e)}")
        raise e

def quality_check_and_regenerate(word: str, meaning: str, options: List[str], config: Dict, max_attempts: int) -> List[str]:
    """생성된 선택지들의 품질을 테스트하고 불량품만 재생성합니다."""
    logger.info(f"🔍 품질 테스트: {options}")
    
    # 품질 테스트 기준
    def is_high_quality(option: str, correct_answer: str, is_correct_answer: bool = False) -> bool:
        # 정답은 품질 테스트에서 제외
        if is_correct_answer:
            return True
            
        if not option or len(option) < 1 or len(option) > 10:
            return False  # 길이 문제
        
        if option == correct_answer:
            return False  # 정답과 동일
        
        if len(option) == 1:  # 한 글자는 품질 낮음
            return False
            
        # 한글이 아닌 문자가 포함된 경우
        if not re.match(r'^[가-힣]+$', option):
            return False
            
        return True
    
    # 품질 테스트 실행
    low_quality_indices = []
    for i, option in enumerate(options):
        # 정답(첫 번째)은 품질 테스트에서 제외
        is_correct = (i == 0)
        if not is_high_quality(option, meaning, is_correct):
            low_quality_indices.append(i)
            logger.warning(f"❌ 품질 낮음 (인덱스 {i}): '{option}'")
    
    # 불량품 재생성
    for idx in low_quality_indices:
        if idx == 0:  # 정답은 건드리지 않음
            continue
            
        logger.info(f"🔄 불량품 재생성 (인덱스 {idx}): '{options[idx]}'")
        
        for attempt in range(max_attempts):
            # 재생성용 프롬프트 (더 구체적)
            regenerate_prompt = f"""다음 영어 단어의 의미와 같은 카테고리에 속하는 고품질 한국어 단어를 1개만 생성해주세요.

단어: {word}
의미: {meaning}
기존 선택지: {options}

생성 규칙:
1. 정답 '{meaning}'과 같은 카테고리의 단어여야 합니다.
2. 기존 선택지와 중복되지 않아야 합니다.
3. 한국어 2-5글자 단어여야 합니다.
4. 1글자나 10글자 이상이면 안 됩니다.
5. 번호, 기호, 영어, 발음 표기 없이 단어만 작성하세요.
6. 실제 존재하는 단어여야 합니다.

예시: apple(사과) → 바나나, 오렌지, 포도"""
            
            try:
                response = generate_with_ollama(regenerate_prompt, config)
                logger.info(f"🤖 재생성 응답 {attempt+1}: {response[:100]}...")
                
                # 응답에서 한글 단어만 추출
                cleaned_response = re.sub(r'\([^)]*\)', '', response)
                cleaned_response = re.sub(r'[a-zA-Z\-]', '', cleaned_response)
                cleaned_response = re.sub(r'[^가-힣]', '', cleaned_response)
                
                if cleaned_response and is_high_quality(cleaned_response, meaning) and cleaned_response not in options:
                    options[idx] = cleaned_response
                    logger.info(f"✅ 재생성 성공: '{cleaned_response}'")
                    break
                else:
                    logger.warning(f"⚠️ 재생성 실패, 재시도 {attempt+1}/{max_attempts}")
                    
            except Exception as e:
                logger.error(f"❌ 재생성 중 오류: {str(e)}")
                continue
    
    return options

 