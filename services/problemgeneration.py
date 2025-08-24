import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils.vocab_utils as vocab_utils
from typing import List, Dict

logger = vocab_utils.logger

# export
def generate_vocabulary(count: int, school_level: str, topic: str = "일반", language: str = "영어") -> List[Dict[str, str]]:
    config = vocab_utils.load_config()

    cmd_config = None
    for cmd in config.get("commands", []):
        if cmd.get("name") == "generate_vocabulary":
            cmd_config = cmd
            break

    if not cmd_config:
        raise ValueError("generate_vocabulary 명령어를 찾을 수 없습니다.")

    logger.info(f"🎯 단어장 생성 시작: count={count}, school_level={school_level}, topic={topic}, language={language}")

    prompt = cmd_config["prompt_template"].format(
        count=count,
        school_level=school_level,
        topic=topic,
        language=language,
    )

    # 최대 3회까지 재시도하여 부족한 개수를 채웁니다.
    aggregated: List[Dict[str, str]] = []
    seen = set()
    max_attempts = 3
    attempts = 0
    while len(aggregated) < count and attempts < max_attempts:
        attempts += 1
        response = vocab_utils.generate_with_gpt(prompt, config)
        vocabulary_data = vocab_utils.parse_vocabulary_response(response)
        for item in vocabulary_data:
            key = (item.get("word"), item.get("meaning"))
            if key not in seen and item.get("word") and item.get("meaning"):
                seen.add(key)
                aggregated.append(item)
            if len(aggregated) >= count:
                break

    if len(aggregated) >= count:
        return aggregated[:count]
    raise ValueError(f"요청한 개수({count})보다 적은 단어({len(aggregated)})가 생성되었습니다.")

# export
def generate_options(word: str, meaning: str) -> List[str]:
    """YAML 프롬프트를 사용하여 단어에 대한 선택지를 동적으로 생성합니다."""
    config = vocab_utils.load_config()

    # 명령어 설정 찾기
    cmd_config = None
    for cmd in config.get("commands", []):
        if cmd.get("name") == "generate_vocabulary_options":
            cmd_config = cmd
            break

    if not cmd_config:
        raise ValueError("generate_vocabulary_options 명령어를 찾을 수 없습니다.")

    logger.info(f"🔍 선택지 생성 시작: 단어='{word}', 의미='{meaning}'")

    prompt = cmd_config["prompt_template"].format(
        word=word,
        meaning=meaning,
    )

    try:
        response = vocab_utils.generate_with_gpt(prompt, config)
        logger.info(f"🤖 AI 응답: {response[:100]}...")

        # 응답 파싱 및 정답 1번 보장
        parsed = vocab_utils.parse_vocabulary_options(response)
        final_options = vocab_utils.ensure_correct_answer_first(parsed, meaning)
        return final_options[:4]
    except Exception as e:
        logger.error(f"❌ 선택지 생성 실패: {str(e)}")
        raise
