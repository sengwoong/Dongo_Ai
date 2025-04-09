import yaml
import os
import requests
import json
from typing import Dict

def load_config():
    """YAML 설정 파일을 로드합니다."""
    try:
        # 현재 디렉토리에서 파일 찾기
        config_path = "EnglishCommand.yaml"
        
        # 파일이 없으면 상위 디렉토리에서 찾기
        if not os.path.exists(config_path):
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "EnglishCommand.yaml")
        
        # 파일이 여전히 없으면 기본 설정 반환
        if not os.path.exists(config_path):
            print("경고: EnglishCommand.yaml 파일을 찾을 수 없습니다. 기본 설정을 사용합니다.")
            return {
                "model": "llama2",
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 500
            }
            
        with open(config_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"경고: YAML 파일을 로드하는 중 오류가 발생했습니다: {e}")
        # 오류 발생 시 기본 설정 반환
        return {
            "model": "llama2",
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 500
        }

def generate_with_ollama(prompt, model="llama2", temperature=0.7, top_p=0.9, max_tokens=500):
    """Ollama를 사용하여 텍스트를 생성합니다."""
    # 임시 구현 - 실제로는 Ollama API를 호출해야 합니다
    return f"Ollama 응답: {prompt[:50]}..."

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