# blobmoni (블랍뭐니?)

Azure Blob Storage 내 다수의 컨테이너를 모니터링하고, 각 컨테이너에 있는 파일들을 관리할 수 있는 Python 프로그램입니다. 이 프로그램은 PyQt5를 사용하여 GUI 기반으로 개발되었으며, 사용자가 Azure Blob Storage의 컨테이너 및 파일을 쉽게 조회하고, 파일 업로드/다운로드/삭제 등의 작업을 할 수 있도록 도와줍니다.

## 주요 기능

- **다중 계정 및 컨테이너 관리**: 여러 Azure Blob Storage 계정을 동시에 관리할 수 있습니다.
    
- **파일 업로드/다운로드/삭제**: 선택한 파일에 대해 업로드, 다운로드, 삭제가 가능합니다.
    
- **컨테이너별 파일 접기/펼치기**: 컨테이너 목록을 접거나 펼칠 수 있는 기능을 제공합니다.
    
- **자동 모니터링**: 설정된 주기(refresh interval)마다 Blob Storage의 상태를 모니터링하고 업데이트합니다.
    
- **직관적인 GUI**: PyQt5를 이용하여 사용자가 쉽게 상호작용할 수 있는 UI를 제공합니다.
    

## 설치 및 실행 방법

### 1. 필수 요구사항

- Python 3.11 이상
    
- Azure Storage Blob Python SDK
    
- PyQt5
    

### 2. 설치

```
# 가상 환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows의 경우 'venv\Scripts\activate'

# 필수 패키지 설치
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일을 생성하여 Azure Blob Storage 연결 정보를 설정합니다. 아래와 같은 형식으로 작성해 주세요.

```
AZURE_CONNECTION_1="DefaultEndpointsProtocol=https;AccountName=your_account_name1;AccountKey=your_account_key1;EndpointSuffix=core.windows.net"
AZURE_CONNECTION_2="DefaultEndpointsProtocol=https;AccountName=your_account_name2;AccountKey=your_account_key2;EndpointSuffix=core.windows.net"
```

### 4. 설정 파일(config.yaml)

`config.yaml` 파일을 생성하여 프로그램 설정을 정의합니다. 예시는 아래와 같습니다:

```
refresh_interval: 60  # 모니터링 주기 (초 단위)
log_level: DEBUG
account_1_containers: []  # 특정 컨테이너만 모니터링하려면 이름을 넣어주세요.
account_2_containers:
- k11
- k12
- k13
```

### 5. 실행

```
python blob_monitor.py
```

## 사용 방법

1. 프로그램 실행 후, 상단에 있는 입력 필드를 통해 모니터링 주기를 변경할 수 있습니다. 변경 후 "적용" 버튼을 누르면 설정이 반영됩니다.
    
2. 각 계정 및 컨테이너에 대해 파일 목록을 확인하고, 파일을 업로드/다운로드/삭제할 수 있습니다.
    
3. 컨테이너명을 더블 클릭하여 해당 컨테이너의 파일 목록을 접거나 펼칠 수 있습니다.
    

## 주요 인터페이스 설명

- **전체 선택**: 현재 컨테이너에 있는 모든 파일을 선택합니다 (컨테이너명은 제외).
    
- **파일 업로드**: 선택한 컨테이너 또는 폴더에 파일을 업로드합니다.
    
- **파일 다운로드**: 선택한 파일들을 로컬 디렉토리에 다운로드합니다.
    
- **파일 삭제**: 선택한 파일들을 Azure Blob Storage에서 삭제합니다.