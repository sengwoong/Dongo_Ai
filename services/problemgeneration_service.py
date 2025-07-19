import yaml
import argparse
import os
import sys
import requests
import json
import re
import random

# 현재 디렉토리의 상위 디렉토리를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# vocab_utils.py 파일을 직접 import
import vocab_utils

def load_commands():
    """YAML 명령어 파일을 로드합니다."""
    return vocab_utils.load_config()

def generate_vocabulary():
    """
    단어장을 생성하는 함수 - 동적 생성 사용
    """
    try:
        # 기본 매개변수 설정
        count = 10
        school_level = "중등"
        
        # 동적 단어장 생성
        vocabulary_data = vocab_utils.generate_vocabulary(count, school_level)
        
        print(f"성공적으로 {len(vocabulary_data)}개의 단어를 생성했습니다.")
        return vocabulary_data
        
    except Exception as e:
        import traceback
        error_msg = f"단어장 생성 중 오류 발생: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        raise RuntimeError(error_msg) from e

def generate_vocabulary_options(word, meaning):
    """단어와 의미를 기반으로 선택지를 동적으로 생성합니다."""
    try:
        # 동적 선택지 생성
        options = vocab_utils.generate_options(word, meaning)
        
        print(f"성공적으로 {len(options)}개의 선택지를 생성했습니다.")
        return options
        
    except Exception as e:
        import traceback
        error_msg = f"선택지 생성 중 오류 발생: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        raise RuntimeError(error_msg) from e

def generate_vocabulary_with_custom_params(count: int, school_level: str):
    """사용자 정의 매개변수로 단어장을 생성합니다."""
    try:
        # 동적 단어장 생성
        vocabulary_data = vocab_utils.generate_vocabulary(count, school_level)
        
        print(f"성공적으로 {len(vocabulary_data)}개의 단어를 생성했습니다.")
        return vocabulary_data
        
    except Exception as e:
        import traceback
        error_msg = f"단어장 생성 중 오류 발생: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        raise RuntimeError(error_msg) from e

def generate_vocabulary_with_options(items: list, userId: str = None, vocaId: str = None):
    """단어 목록에 대한 선택지를 포함한 단어장을 생성합니다."""
    try:
        result = []
        
        for item in items:
            word = item.get("word", "")
            meaning = item.get("meaning", "")
            
            if not word or not meaning:
                continue
            
            try:
                # 각 단어에 대한 선택지 생성
                options = vocab_utils.generate_options(word, meaning)
                
                result.append({
                    "word": word,
                    "meaning": meaning,
                    "options": options
                })
                
            except Exception as e:
                print(f"단어 '{word}'의 선택지 생성 실패: {str(e)}")
                # 선택지 생성 실패 시 에러를 그대로 전파
                raise RuntimeError(f"단어 '{word}'의 선택지 생성 실패: {str(e)}")
        
        return result
        
    except Exception as e:
        import traceback
        error_msg = f"선택지 포함 단어장 생성 중 오류 발생: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        raise RuntimeError(error_msg) from e

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
    
    # 명령어 실행
    try:
        if args.command == "generate_vocabulary":
            count = getattr(args, 'count', 10)
            school_level = getattr(args, 'school_level', '중등')
            result = generate_vocabulary_with_custom_params(count, school_level)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
        elif args.command == "generate_vocabulary_options":
            word = getattr(args, 'word', '')
            meaning = getattr(args, 'meaning', '')
            if word and meaning:
                result = generate_vocabulary_options(word, meaning)
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print("word와 meaning 매개변수가 필요합니다.")
                
        else:
            print(f"지원하지 않는 명령어: {args.command}")
            
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        sys.exit(1)