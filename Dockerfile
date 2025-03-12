# ndm2blob/Dockerfile

FROM python:3.8-slim

# 작업 디렉토리 설정
WORKDIR /app

# 종속성 파일 복사
COPY requirements.txt requirements-dev.txt ./

# 종속성 설치
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install -r requirements-dev.txt

# 소스 코드 복사
COPY src/ src/
COPY configs/ configs/
COPY scripts/ scripts/

# 실행 스크립트 복사
COPY scripts/run.py scripts/run.py

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1

# 컨테이너 시작 시 실행할 명령
CMD ["python", "scripts/run.py"]
