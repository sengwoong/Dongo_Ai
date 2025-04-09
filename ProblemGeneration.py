import yaml
import argparse
from llama_cpp import Llama
import os
import sys

def load_commands():
    """YAML 파일에서 명령어 설정을 로드합니다."""
    try:
        with open("commands.yaml", "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"YAML 파일을 로드하는 중 오류가 발생했습니다: {e}")
        sys.exit(1)

def initialize_model(config):
    """Llama 모델을 초기화합니다."""
    model_path = config["model"]["path"]
    
    if not os.path.exists(model_path):
        print(f"모델 파일을 찾을 수 없습니다: {model_path}")
        print("모델을 다운로드하거나 올바른 경로를 지정해주세요.")
        sys.exit(1)
    
    try:
        model = Llama(
            model_path=model_path,
            n_ctx=config["model"]["context_length"],
            verbose=False
        )
        return model
    except Exception as e:
        print(f"모델을 초기화하는 중 오류가 발생했습니다: {e}")
        sys.exit(1)

def generate_words(model, command, args):
    """지정된 명령어와 매개변수를 사용하여 단어를 생성합니다."""
    # 명령어 찾기
    cmd_config = None
    for cmd in config["commands"]:
        if cmd["name"] == command:
            cmd_config = cmd
            break
    
    if cmd_config is None:
        print(f"알 수 없는 명령어입니다: {command}")
        return
    
    # 매개변수 처리
    params = {}
    for param in cmd_config["parameters"]:
        param_name = param["name"]
        if hasattr(args, param_name) and getattr(args, param_name) is not None:
            params[param_name] = getattr(args, param_name)
        elif "default" in param:
            params[param_name] = param["default"]
        elif param.get("required", False):
            print(f"필수 매개변수가 누락되었습니다: {param_name}")
            return
    
    # 학교 수준에 따른 난이도 조정
    school_level = params.get("school_level", "중등")
    if school_level == "초등":
        difficulty = "쉬운"
        grade_range = "1-6학년"
    elif school_level == "중등":
        difficulty = "중간"
        grade_range = "7-9학년"
    elif school_level == "고등":
        difficulty = "어려운"
        grade_range = "10-12학년"
    else:
        difficulty = "중간"
        grade_range = "전체"
    
    # 프롬프트에 학교 수준 정보 추가
    params["difficulty"] = difficulty
    params["grade_range"] = grade_range
    
    # 프롬프트 생성
    prompt = cmd_config["prompt_template"].format(**params)
    
    print(f"학교 수준: {school_level} ({grade_range}, {difficulty} 난이도)")
    print(f"프롬프트: {prompt}")
    print("생성 중...")
    
    # 모델로 텍스트 생성
    output = model.create_completion(
        prompt,
        max_tokens=config["model"]["max_tokens"],
        temperature=config["model"]["temperature"],
        top_p=config["model"]["top_p"],
        echo=False
    )
    
    # 결과 출력
    generated_text = output["choices"][0]["text"].strip()
    print("\n생성된 단어:")
    print(generated_text)

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
    
    # 모델 초기화
    model = initialize_model(config)
    
    # 단어 생성
    generate_words(model, args.command, args) 