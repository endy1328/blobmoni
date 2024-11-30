import logging
import re
from azure.storage.blob import BlobServiceClient, BlobClient
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QListWidgetItem, QMenu, QApplication
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QCursor
import os

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class BlobStorageHandler:
    def __init__(self, config):
        self.config = config

    def initialize_blob_clients(self):
        """Azure Blob 서비스 클라이언트를 초기화합니다."""
        clients = []
        account_index = 1
        while True:
            connection_string = os.getenv(f"AZURE_CONNECTION_{account_index}")

            if not connection_string:
                break

            try:
                client = BlobServiceClient.from_connection_string(connection_string)
                account_name = client.account_name
                containers = self.config.get(f'account_{account_index}_containers')
                if not containers:
                    containers = [container.name for container in client.list_containers()]
                clients.append({
                    'account_name': account_name,
                    'client': client,
                    'containers': containers
                })
                logging.debug(f"계정 {account_name} 초기화 성공. 컨테이너: {containers}")
            except Exception as e:
                logging.error(f"오류: 계정 {account_index} 초기화 중 문제가 발생했습니다. 오류 내용: {e}")

            account_index += 1

        return clients

    def upload_file(self, list_widget, account, container_name=None):
        """파일 탐색기를 열어 선택한 파일을 업로드합니다."""
        logging.debug(f"파일 업로드 시도. 계정: {account['account_name']}")
        
        # 컨테이너가 명시되지 않은 경우 선택된 항목에서 추출
        if container_name is None:
            selected_items = list_widget.selectedItems()
            if not selected_items:
                QMessageBox.warning(list_widget, "오류", "업로드할 경로를 선택하세요.")
                return

            target_path_item = selected_items[-1]
            target_path = target_path_item.text()

            if target_path.startswith("====="):
                container_name = target_path.split(":")[1].strip()  # 컨테이너 이름만 추출
                blob_name_prefix = ""  # 최상위 디렉토리에 업로드
            elif "/" not in target_path:
                container_name = target_path.strip()
                blob_name_prefix = ""
            else:
                try:
                    container_name, blob_path_prefix = target_path.split("/", 1)
                    blob_name_prefix = os.path.dirname(blob_path_prefix)
                except ValueError:
                    QMessageBox.warning(list_widget, "오류", "올바른 경로를 선택하세요.")
                    return
        else:
            blob_name_prefix = ""  # 명시된 컨테이너에는 최상위에 업로드

        # 파일 선택 (다중 파일 가능)
        file_paths, _ = QFileDialog.getOpenFileNames(list_widget, "파일 선택")
        if not file_paths:
            return  # 파일 선택 취소

        try:
            container_client = account['client'].get_container_client(container_name)

            for file_path in file_paths:
                # 파일 이름 생성
                blob_name = f"{blob_name_prefix}/{os.path.basename(file_path)}" if blob_name_prefix else os.path.basename(file_path)

                # 유효한 Blob 이름을 보장하기 위해 공백 및 잘못된 문자 제거
                blob_name = re.sub(r'[^a-zA-Z0-9_\-/. ]', '_', blob_name)  # 유효하지 않은 문자는 '_'로 대체
                blob_name = blob_name.strip('/')  # 앞뒤의 슬래시 제거

                # Azure Blob Storage에서는 Blob 이름에 연속된 슬래시나 특정 문자 패턴이 문제가 될 수 있음
                if not self.is_valid_blob_name(blob_name):
                    QMessageBox.warning(list_widget, "오류", f"유효하지 않은 Blob 이름입니다: {blob_name}")
                    logging.warning(f"유효하지 않은 Blob 이름으로 업로드 시도됨: {blob_name}")
                    continue

                # 파일 업로드
                with open(file_path, "rb") as data:
                    container_client.upload_blob(name=blob_name, data=data, overwrite=True)

                logging.info(f"파일 업로드 성공: {blob_name}")
                QMessageBox.information(list_widget, "알림", f"파일이 업로드되었습니다: {blob_name}")

        except Exception as e:
            QMessageBox.critical(list_widget, "오류", f"파일 업로드 실패: {e}")
            logging.error(f"파일 업로드 실패: {e}")

    def is_valid_blob_name(self, blob_name):
        """Azure Blob Storage의 유효한 Blob 이름인지 확인합니다."""
        if len(blob_name) > 1024:
            return False
        if re.search(r'//', blob_name):  # 연속된 슬래시가 있는 경우 유효하지 않음
            return False
        if blob_name.startswith('.') or blob_name.endswith('.'):  # 이름이 '.'로 시작하거나 끝나면 안 됨
            return False
        if blob_name.startswith(' ') or blob_name.endswith(' '):  # 이름이 공백으로 시작하거나 끝나면 안 됨
            return False
        return True

    def delete_selected_files(self, list_widget, account):
        """선택한 파일을 삭제합니다."""
        logging.debug(f"선택한 파일 삭제 시도. 계정: {account['account_name']}")
        selected_items = list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(list_widget, "알림", "삭제할 파일을 선택하세요.")
            return

        for item in selected_items:
            file_path = item.text()

            if file_path.startswith("=====") or "[오류]" in file_path:
                continue

            try:
                container, blob_path = file_path.split("/", 1)
                container_client = account['client'].get_container_client(container)
                container_client.delete_blob(blob_path)
                list_widget.takeItem(list_widget.row(item))
                logging.info(f"삭제 성공: {file_path}")
            except Exception as e:
                logging.error(f"삭제 실패: {file_path}, 이유: {e}")
                QMessageBox.warning(list_widget, "오류", f"파일 삭제 실패: {file_path}\n{e}")

        QMessageBox.information(list_widget, "알림", "선택한 파일이 삭제되었습니다.")

    def download_file(self, list_widget, account):
        """선택한 파일을 다운로드합니다."""
        logging.debug(f"선택한 파일 다운로드 시도. 계정: {account['account_name']}")
        selected_items = list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(list_widget, "알림", "다운로드할 파일을 선택하세요.")
            return

        for item in selected_items:
            file_path = item.text()

            if file_path.startswith("=====") or "[오류]" in file_path:
                continue

            try:
                container, blob_path = file_path.split("/", 1)
                container_client = account['client'].get_container_client(container)
                blob_client = container_client.get_blob_client(blob_path)

                save_path, _ = QFileDialog.getSaveFileName(list_widget, "파일 저장", os.path.basename(blob_path))
                if not save_path:
                    continue  # 저장 경로를 선택하지 않은 경우

                with open(save_path, "wb") as file:
                    data = blob_client.download_blob()
                    file.write(data.readall())

                logging.info(f"다운로드 성공: {blob_path} -> {save_path}")
                QMessageBox.information(list_widget, "알림", f"파일이 다운로드되었습니다: {save_path}")
            except Exception as e:
                logging.error(f"다운로드 실패: {file_path}, 이유: {e}")
                QMessageBox.warning(list_widget, "오류", f"파일 다운로드 실패: {file_path}\n{e}")

    def update_blobs(self, account, list_widget):
        """모든 계정과 컨테이너의 블랍 목록을 업데이트합니다."""
        logging.debug(f"블랍 목록 업데이트 시도. 계정: {account['account_name']}")
        for container in account['containers']:
            try:
                logging.debug(f"컨테이너 접근 시도: {container}")
                container_client = account['client'].get_container_client(container)
                blobs = container_client.list_blobs()
                separator = QListWidgetItem(f"===== 컨테이너: {container} =====")
                separator.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # 선택 가능하도록 플래그 설정
                list_widget.addItem(separator)

                has_blobs = False
                for blob in blobs:
                    has_blobs = True
                    logging.debug(f"블랍 추가: {blob.name}")
                    list_widget.addItem(f"{container}/{blob.name}")

                if not has_blobs:
                    logging.debug(f"컨테이너 '{container}'에 파일이 없습니다.")
                    list_widget.addItem(f"{container}: 파일이 없습니다.")

            except Exception as e:
                logging.error(f"[오류] 컨테이너 접근 실패: {container}, 오류 메시지: {str(e)}")
                error_item = QListWidgetItem(f"[오류] 컨테이너 접근 실패: {container}, 메시지: {str(e)}")
                error_item.setForeground(Qt.red)
                list_widget.addItem(error_item)

    def context_menu_event(self, list_widget, event, account):
        """마우스 오른쪽 버튼 클릭 시 팝업 메뉴를 표시합니다."""
        selected_items = list_widget.selectedItems()
        if not selected_items:
            return

        menu = QMenu(list_widget)
        copy_action = menu.addAction("파일 경로 복사")
        download_action = menu.addAction("파일 다운로드")
        delete_action = menu.addAction("파일 삭제")

        action = menu.exec_(QCursor.pos())

        if action == copy_action:
            self.copy_file_path_to_clipboard(selected_items)
        elif action == download_action:
            self.download_file(list_widget, account)
        elif action == delete_action:
            self.delete_selected_files(list_widget, account)

    def copy_file_path_to_clipboard(self, selected_items):
        """선택한 파일의 경로를 클립보드에 복사합니다."""
        paths = [item.text() for item in selected_items if not item.text().startswith("=====") and "[오류]" not in item.text()]
        if paths:
            clipboard = QApplication.clipboard()
            clipboard.setText("\n".join(paths))
            logging.info(f"파일 경로 복사: {paths}")
            QMessageBox.information(None, "알림", "파일 경로가 클립보드에 복사되었습니다.")
