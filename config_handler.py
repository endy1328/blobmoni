import yaml
import os
import sys
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ConfigHandler:
    def __init__(self, config_path):
        self.config_path = config_path

    def load_env(self):
        """환경 변수를 .env 파일에서 로드합니다."""
        load_dotenv()
        logging.debug(".env 파일 로드 완료")

    def load_config(self):
        """config.yaml 파일에서 설정값을 읽어옵니다."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                logging.debug("config.yaml 파일 로드 성공")
                return yaml.safe_load(f)
        except FileNotFoundError:
            logging.error("오류: config.yaml 파일을 찾을 수 없습니다.")
            sys.exit(1)

    def save_config(self, config):
        """현재 설정값을 config.yaml 파일에 저장합니다."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True)
                logging.debug("config.yaml 파일 저장 성공")
        except Exception as e:
            logging.error(f"오류: config.yaml 저장 중 문제가 발생했습니다. {e}")
