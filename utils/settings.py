import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리 기준
ROOT_DIR = Path(__file__).resolve().parents[1]

# .env 로드
load_dotenv(dotenv_path=ROOT_DIR / ".env")

# config.yml 로드
CONFIG_PATH = ROOT_DIR / "_config.yml"
with open(CONFIG_PATH, "r") as f:
    raw_config = yaml.safe_load(f)

# 환경변수 치환
def resolve_env(value):
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        return os.getenv(value[2:-1], "")
    return value

def resolve_nested(d):
    for k, v in d.items():
        if isinstance(v, dict):
            d[k] = resolve_nested(v)
        else:
            d[k] = resolve_env(v)
    return d

# 최종 config 객체
CONFIG = resolve_nested(raw_config)

# DB 설정 불러오기
POSTGRES_CONFIG = CONFIG.get("database", {}).get("postgresql", {})
SQLITE_CONFIG = CONFIG.get("database", {}).get("sqlite", {})
REDIS_CONFIG = CONFIG.get("redis", {})