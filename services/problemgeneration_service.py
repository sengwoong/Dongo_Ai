import yaml
import argparse
import os
import sys
import requests
import json
import re
import random
from Gpt.utils import (
    clean_meaning,
    clean_option,
    ensure_correct_answer_first,
    get_default_options_from_config,
    guess_category_from_config,
    generate_default_options,
    guess_category,
    generate_default_options_with_exact_meaning,
    ensure_four_options_with_exact_meaning
)

def load_commands():
    """YAML 명령어 파일을 로드합니다."""
    try:
        # 여러 경로에서 파일 찾기
        possible_paths = [
            "EnglishCommand.yaml",  # 현재 디렉토리
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "EnglishCommand.yaml"),  # services 디렉토리
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "EnglishCommand.yaml")  # 프로젝트 루트
        ]
        
        yaml_path = None
        for path in possible_paths:
            if os.path.exists(path):
                yaml_path = path
                break
        
        if yaml_path is None:
            print("경고: EnglishCommand.yaml 파일을 찾을 수 없습니다. 기본 설정을 사용합니다.")
            return {
                "model": {
                    "name": "llama2",
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            }
            
        with open(yaml_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"경고: YAML 파일을 로드하는 중 오류가 발생했습니다: {e}")
        # 오류 발생 시 기본 설정 반환
        return {
            "model": {
                "name": "llama2",
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 500
            }
        }

def generate_vocabulary():
    """
    단어장을 생성하는 함수 - EnglishCommand.yaml 설정에 따라 단어장 생성
    """
    try:
        # EnglishCommand.yaml 파일 로드
        config = load_commands()
        
        # generate_vocabulary 명령어 찾기
        cmd_config = None
        for cmd in config.get("commands", []):
            if cmd.get("name") == "generate_vocabulary":
                cmd_config = cmd
                break
        
        if not cmd_config:
            error_msg = "generate_vocabulary 명령어를 찾을 수 없습니다."
            print(error_msg)
            raise ValueError(error_msg)
        
        # 기본 매개변수 설정
        params = {}
        for param in cmd_config.get("parameters", []):
            if "default" in param:
                params[param["name"]] = param["default"]
        
        # 학교 수준에 따른 난이도 조정
        school_level = params.get("school_level", "중등")
        
        # 프롬프트 생성 - 템플릿 사용
        prompt = cmd_config["prompt_template"].format(**params)
        
        # 모델 설정 가져오기
        model_name = config["model"]["name"]
        temperature = config["model"]["temperature"]
        top_p = config["model"]["top_p"]
        max_tokens = config["model"]["max_tokens"]
        
        print(f"프롬프트: {prompt}")
        print(f"모델: {model_name}, 온도: {temperature}")
        
        # Ollama API 호출
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "stream": False
            }
        )
        
        if response.status_code != 200:
            error_msg = f"API 호출 실패: {response.status_code}, 응답: {response.text}"
            print(error_msg)
            raise RuntimeError(error_msg)
        
        # 응답 파싱
        response_json = response.json()
        generated_text = response_json.get("response", "")
        
        # 생성된 텍스트 출력
        print(f"생성된 텍스트: {generated_text[:100]}...")
        
        # 텍스트 파싱
        vocabulary_data = parse_vocabulary_data(generated_text)
        
        return vocabulary_data
        
    except Exception as e:
        import traceback
        error_msg = f"단어장 생성 중 오류 발생: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        
        # 오류를 전파
        raise RuntimeError(error_msg) from e

def parse_vocabulary_data(text):
    """생성된 텍스트에서 단어장 데이터를 파싱합니다."""
    vocabulary_data = []
    
    # 응답 형식 분석
    print("파싱 시작...")
    
    # 번호가 붙은 형식 처리 (예: "1. Word: "Creative"")
    numbered_pattern = r'(\d+)\.\s+Word:\s+"([^"]+)"\s+Meaning:\s+([^\.]+)'
    numbered_matches = re.findall(numbered_pattern, text, re.IGNORECASE)
    
    if numbered_matches:
        print(f"번호 형식 매치 발견: {len(numbered_matches)}개")
        for match in numbered_matches:
            item = {
                "word": match[1].strip(),
                "meaning": clean_meaning(match[2].strip()),
                "example": ""
            }
            vocabulary_data.append(item)
    
    # 기존 형식 처리 (단어: / 의미:)
    if not vocabulary_data:
        print("기존 형식으로 파싱 시도...")
        current_item = {}
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                if current_item and "word" in current_item and "meaning" in current_item:
                    # 예문이 없는 경우 빈 문자열 추가
                    if "example" not in current_item:
                        current_item["example"] = ""
                    vocabulary_data.append(current_item)
                    current_item = {}
                continue
                
            if ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    key, value = parts
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == "단어" or key == "word":
                        if current_item and "word" in current_item and "meaning" in current_item:
                            if "example" not in current_item:
                                current_item["example"] = ""
                            vocabulary_data.append(current_item)
                            current_item = {}
                        # 따옴표 제거
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        current_item["word"] = value
                    elif key == "의미" or key == "meaning":
                        current_item["meaning"] = clean_meaning(value)
                    elif key == "예문" or key == "example" or key == "영어" or key == "english":
                        current_item["example"] = value
    
        # 마지막 항목 추가
        if current_item and "word" in current_item and "meaning" in current_item:
            if "example" not in current_item:
                current_item["example"] = ""
            vocabulary_data.append(current_item)
    
    # 추가 형식 처리 - 번호 + Word/Meaning 형식 (예: "1. Word: Creative")
    if not vocabulary_data:
        print("추가 형식으로 파싱 시도...")
        pattern = r'(\d+)\.\s+Word:\s+"?([^"\n]+)"?\s+Meaning:\s+([^\.\n]+)'
        matches = re.findall(pattern, text)
        
        for match in matches:
            item = {
                "word": match[1].strip(),
                "meaning": match[2].strip(),
                "example": ""
            }
            vocabulary_data.append(item)
    
    print(f"최종 파싱 결과: {len(vocabulary_data)}개 항목")
    return vocabulary_data

def generate_vocabulary_options(word, meaning):
    """단어와 의미를 기반으로 선택지를 생성합니다."""
    try:
        # 명령어 설정 로드
        config = load_commands()
        
        # generate_vocabulary_options 명령어 찾기
        cmd_config = None
        for cmd in config.get("commands", []):
            if cmd.get("name") == "generate_vocabulary_options":
                cmd_config = cmd
                break
        
        if not cmd_config:
            error_msg = "generate_vocabulary_options 명령어를 찾을 수 없습니다."
            print(error_msg)
            raise ValueError(error_msg)
        
        # 프롬프트 생성
        prompt = cmd_config["prompt_template"].format(word=word, meaning=meaning)
        
        # 모델 설정 가져오기
        model_name = config["model"]["name"]
        temperature = config["model"]["temperature"]
        top_p = config["model"]["top_p"]
        max_tokens = config["model"]["max_tokens"]
        
        print(f"단어: {word}, 의미: {meaning}")
        print(f"모델: {model_name}, 온도: {temperature}")
        
        # Ollama API 호출
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "stream": False
            }
        )
        
        if response.status_code != 200:
            error_msg = f"API 호출 실패: {response.status_code}, 응답: {response.text}"
            print(error_msg)
            raise RuntimeError(error_msg)
        
        # 응답 파싱
        response_json = response.json()
        generated_text = response_json.get("response", "")
        
        # 생성된 텍스트 출력 (디버깅용)
        print(f"생성된 텍스트: {generated_text[:300]}...")
        
        # 응답에서 선택지만 추출
        options = extract_options_from_text(generated_text, meaning)
        
        # 선택지가 없거나 충분하지 않으면 config에서 기본 선택지 가져오기
        if not options or len(options) < 4:
            print("선택지 추출 실패, 기본 선택지 사용")
            # 설정 파일에서 기본 선택지 가져오기
            from config import DEFAULT_OPTIONS
            
            # 기본 선택지 생성
            options = get_default_options_from_config(meaning, DEFAULT_OPTIONS)
            
            if not options or len(options) < 4:
                error_msg = f"선택지 생성 실패: 추출된 선택지가 부족합니다. 원본 텍스트: {generated_text[:100]}"
                print(error_msg)
                raise ValueError(error_msg)
        
        return options
        
    except Exception as e:
        import traceback
        error_msg = f"선택지 생성 중 오류 발생: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        
        # 오류를 상위로 전파
        raise RuntimeError(error_msg) from e

def extract_options_from_text(text, correct_answer):
    """LLM 응답에서 선택지만 추출하는 함수"""
    # 1. 정규 표현식으로 선택지 패턴 찾기
    options_pattern = r'([^,\n]+)(,\s*[^,\n]+){3,}'
    matches = re.findall(options_pattern, text)
    
    if matches:
        first_match = matches[0]
        if isinstance(first_match, tuple):
            # 첫 번째 매치가 튜플이면 첫 번째 요소와 나머지를 합침
            options_text = first_match[0] + ''.join(first_match[1:])
        else:
            options_text = first_match
    else:
        # 2. 쉼표로 구분된 첫 번째 라인 시도
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines:
            if ',' in line and len(line.split(',')) >= 3:
                options_text = line
                break
        else:
            # 3. 번호가 있는 목록 (1. 2. 3. 등) 시도
            number_pattern = r'\d+\.\s*([^\d\n]+)'
            num_matches = re.findall(number_pattern, text)
            if len(num_matches) >= 3:
                return ensure_correct_answer_first([clean_option(m.strip()) for m in num_matches[:4]], correct_answer)
            return []
    
    # 선택지 분리
    options = [opt.strip() for opt in options_text.split(',')]
    
    # 선택지 정제 (불필요한 프리픽스 등 제거)
    cleaned_options = []
    for opt in options:
        cleaned_opt = clean_option(opt)
        
        # 중복 선택지 제거 및 정답과 동일한 선택지 제거 (정답은 나중에 추가)
        if cleaned_opt and cleaned_opt not in cleaned_options and cleaned_opt != correct_answer:
            cleaned_options.append(cleaned_opt)
    
    # 정답을 맨 앞에 추가
    cleaned_options.insert(0, correct_answer)
    
    # 최대 4개 선택지만 사용
    return cleaned_options[:4]

def generate_default_options(meaning):
    """기본 선택지 생성"""
    from config import DEFAULT_OPTIONS
    
    # 의미 카테고리 추측
    category = guess_category(meaning)
    
    # 카테고리에 맞는 기본 옵션 사용
    if category in DEFAULT_OPTIONS:
        options = [meaning]
        for opt in DEFAULT_OPTIONS[category]:
            if opt != meaning and len(options) < 4:
                options.append(opt)
    else:
        # 카테고리를 찾을 수 없으면 기본 옵션 사용
        options = [meaning, "포도", "바나나", "딸기"]
    
    # 옵션이 4개가 안되면 추가
    while len(options) < 4:
        fallback = ["학교", "책", "펜", "노트"]
        for opt in fallback:
            if opt not in options and len(options) < 4:
                options.append(opt)
    
    return options

def generate_default_options_with_exact_meaning(meaning):
    """
    정확한 meaning을 포함한 기본 선택지를 생성하는 함수
    """
    # 괄호가 있는 경우 괄호 앞 부분만 사용
    meaning_clean = meaning.split('(')[0].strip()
    
    # 특정 단어에 대한 맞춤형 선택지 생성
    if meaning_clean in ["중등", "중학생"]:
        return [
            meaning,
            "초등",
            "고등",
            "대학생"
        ]
    elif meaning_clean in ["초등", "초등학생"]:
        return [
            meaning,
            "중등",
            "고등",
            "유치원생"
        ]
    elif meaning_clean in ["고등", "고등학생"]:
        return [
            meaning,
            "중등",
            "대학생",
            "초등"
        ]
    elif "학생" in meaning_clean:
        return [
            meaning,
            "선생님",
            "교수",
            "학부모"
        ]
    elif "도시" in meaning_clean:
        return [
            meaning,
            "시골",
            "마을",
            "농촌"
        ]
    
    # 기본 선택지 생성 (의미적으로 관련 없는 단어들)
    common_words = [
        "학교", "공부", "시험", "숙제",
        "책", "연필", "노트", "교실",
        "선생님", "학생", "친구", "가족",
        "집", "도시", "나라", "세계"
    ]
    
    # meaning과 관련 없는 단어 선택
    options = [meaning]
    random.shuffle(common_words)
    
    for word in common_words:
        if len(options) >= 4:
            break
        if word != meaning_clean and word not in options:
            options.append(word)
    
    # 여전히 선택지가 부족한 경우 기존 방식으로 생성
    if len(options) < 4:
        remaining = 4 - len(options)
        additional = [
            f"다른 {meaning_clean}",
            f"새로운 {meaning_clean}",
            f"특별한 {meaning_clean}",
            f"중요한 {meaning_clean}"
        ]
        
        for i in range(min(remaining, len(additional))):
            options.append(additional[i])
    
    return options

def ensure_four_options_with_exact_meaning(options_list, meaning):
    """
    정확한 meaning을 포함하고 선택지가 4개가 되도록 보장하는 함수
    """
    # 정확한 meaning이 첫 번째 항목인지 확인
    if options_list[0] != meaning:
        if meaning in options_list:
            options_list.remove(meaning)
        options_list.insert(0, meaning)
    
    # 선택지가 4개 미만인 경우 추가 선택지 생성
    if len(options_list) < 4:
        meaning_clean = meaning.split('(')[0].strip()
        additional_options = [
            f"다른 {meaning_clean}",
            f"새로운 {meaning_clean}",
            f"특별한 {meaning_clean}",
            f"중요한 {meaning_clean}"
        ]
        
        # 필요한 만큼 추가 선택지 추가
        for opt in additional_options:
            if len(options_list) >= 4:
                break
            if opt not in options_list:
                options_list.append(opt)
    
    # 선택지가 4개를 초과하는 경우 처음 4개만 사용
    return options_list[:4]

if __name__ == "__main__":
    # 설정 로드
    config = load_commands()
    
    # 명령행 인수 파서 설정
    parser = argparse.ArgumentParser(description=config["program"]["description"])
    subparsers = parser.add_subparsers(dest="command", help="실행할 명령어")
    
    # 각 명령어에 대한 하위 파서 생성
    for cmd in config["commands"]:
        cmd_parser = subparsers.add_parser(cmd["name"], help=cmd["description"])
        
        # 학교 수준 매개변수 추가
        cmd_parser.add_argument(
            "--school_level",
            type=str,
            choices=["초등", "중등", "고등"],
            default="중등",
            help="학교 수준 (초등, 중등, 고등)"
        )
        
        for param in cmd["parameters"]:
            if param["name"] == "school_level":
                continue  # 이미 추가했으므로 건너뜀
                
            if param["type"] == "integer":
                cmd_parser.add_argument(
                    f"--{param['name']}", 
                    type=int,
                    help=param["description"],
                    default=param.get("default"),
                    required=param.get("required", False)
                )
            else:
                cmd_parser.add_argument(
                    f"--{param['name']}", 
                    type=str,
                    help=param["description"],
                    default=param.get("default"),
                    required=param.get("required", False)
                )
    
    # 인수 파싱
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(0)