import sys
import threading
import time
import logging
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QSplitter, QPushButton, QMessageBox, QHBoxLayout, QLineEdit, QAbstractItemView, QListWidget, QMenu, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from blob_storage import BlobStorageHandler
from config_handler import ConfigHandler
import re

# 로그 설정
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class BlobMonitor(QWidget):
    VERSION = "1.0"

    def __init__(self):
        super().__init__()
        logging.debug("BlobMonitor 초기화 시작")
        
        self.config_handler = ConfigHandler("config.yaml")
        self.config_handler.load_env()
        self.config = self.config_handler.load_config()
        self.refresh_interval = self.config['refresh_interval']

        # 디버그 레벨 설정 추가
        log_level = self.config.get('log_level', 'DEBUG').upper()
        numeric_level = getattr(logging, log_level, logging.DEBUG)
        logging.getLogger().setLevel(numeric_level)

        self.blob_handler = BlobStorageHandler(self.config)
        self.blob_service_clients = self.blob_handler.initialize_blob_clients()

        self.layout_orientation = Qt.Vertical  # 초기 레이아웃 방향
        self.single_account_mode = None  # 특정 계정만 표시하는 모드 여부
        self.init_ui()  # UI 초기화
        self.start_monitoring()  # 모니터링 시작

        logging.debug("BlobMonitor 초기화 완료")

    def init_ui(self):
        """프로그램 UI를 초기화합니다."""
        logging.debug("UI 초기화 시작")
        self.setWindowTitle(f'blobmoni (블랍뭐니?) - v{self.VERSION}')
        self.main_layout = QVBoxLayout()

        # 상단 입력 필드 및 버튼
        self.control_layout = QHBoxLayout()
        self.version_label = QLabel(f"버전: {self.VERSION}")
        self.interval_label = QLabel(f"현재 refresh_interval: {self.refresh_interval} 초")
        self.interval_input = QLineEdit()
        self.interval_input.setPlaceholderText("새 refresh_interval 입력 (초 단위)")
        self.interval_button = QPushButton("적용")
        self.interval_button.clicked.connect(self.update_refresh_interval)
        self.refresh_now_button = QPushButton("지금")
        self.refresh_now_button.clicked.connect(self.update_blobs)
        self.layout_toggle_button = QPushButton("가로로 변경")
        self.layout_toggle_button.clicked.connect(self.toggle_layout_orientation)

        self.control_layout.addWidget(self.version_label)
        self.control_layout.addWidget(self.interval_label)
        self.control_layout.addWidget(self.interval_input)
        self.control_layout.addWidget(self.interval_button)
        self.control_layout.addWidget(self.refresh_now_button)
        self.control_layout.addWidget(self.layout_toggle_button)

        self.main_layout.addLayout(self.control_layout)

        # 메인 화면
        self.account_splitter = QSplitter(self.layout_orientation)
        self.account_widgets = []

        for account in self.blob_service_clients:
            account_layout = QVBoxLayout()
            account_label = QLabel(f"계정: {account['account_name']}")
            account_label.setStyleSheet("font-weight: bold;")
            account_label.mouseDoubleClickEvent = lambda event, acc=account: self.toggle_single_account_mode(event, acc)
            list_widget = QListWidget()
            list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)  # 다중 선택 가능

            # 마우스 오른쪽 클릭 시 팝업 메뉴 표시
            list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
            list_widget.customContextMenuRequested.connect(lambda position, lst=list_widget, acc=account: self.show_context_menu(position, lst, acc))

            self.account_widgets.append((account_label, list_widget, account))

            button_layout = QHBoxLayout()  # 버튼 레이아웃
            button_layout.setSpacing(10)  # 버튼 간격 조정

            select_all_button = QPushButton("전체 선택")
            select_all_button.setFixedHeight(35)
            select_all_button.clicked.connect(lambda _, lst=list_widget: self.select_all_files(lst))

            button_layout.addWidget(select_all_button)

            button_widget = QWidget()
            button_widget.setLayout(button_layout)
            button_widget.setStyleSheet("QWidget { margin: 0 auto; }")

            account_widget = QWidget()
            account_layout.addWidget(account_label)
            account_layout.addWidget(list_widget)
            account_layout.addWidget(button_widget)
            account_widget.setLayout(account_layout)
            self.account_splitter.addWidget(account_widget)

        self.main_layout.addWidget(self.account_splitter)
        self.setLayout(self.main_layout)
        self.resize(1200, 800)
        self.show()

        logging.debug("UI 초기화 완료")

    def show_context_menu(self, position, list_widget, account):
        """마우스 오른쪽 클릭 시 팝업 메뉴를 표시합니다."""
        selected_items = list_widget.selectedItems()
        
        menu = QMenu(self)

        if not selected_items or selected_items[0].text().startswith("====="):
            # 컨테이너가 선택된 경우 파일 업로드만 표시
            upload_action = menu.addAction("파일 업로드")
            container_name = re.search(r'===== 컨테이너:(.+?) =====', selected_items[0].text()).group(1).strip()
        else:
            # 파일이 선택된 경우 모든 메뉴 항목 표시
            copy_action = menu.addAction("파일 경로 복사")
            download_action = menu.addAction("파일 다운로드")
            delete_action = menu.addAction("파일 삭제")
            upload_action = menu.addAction("파일 업로드")
            container_name = None

        action = menu.exec_(list_widget.viewport().mapToGlobal(position))

        if action == upload_action:
            if container_name:
                # 컨테이너 이름만 추출한 경우 해당 컨테이너로 업로드
                self.blob_handler.upload_file(list_widget, account, container_name=container_name)
            else:
                # 일반적인 업로드
                self.blob_handler.upload_file(list_widget, account)
        elif 'copy_action' in locals() and action == copy_action:
            self.blob_handler.copy_file_path_to_clipboard(selected_items)
        elif 'download_action' in locals() and action == download_action:
            self.download_files(list_widget, account, selected_items)
        elif 'delete_action' in locals() and action == delete_action:
            self.blob_handler.delete_selected_files(list_widget, account)

    def upload_file(self, list_widget, account):
        """파일 업로드 처리를 담당합니다."""
        selected_items = list_widget.selectedItems()
        container_name = None

        if selected_items:
            target_path = selected_items[-1].text()

            if target_path.startswith("====="):
                container_name = target_path.split(":")[1].strip()  # 컨테이너 이름만 추출
            elif "/" not in target_path:
                container_name = target_path.strip()
        
        # BlobStorageHandler의 upload_file 호출 시 container_name 전달
        result = self.blob_handler.upload_file(list_widget, account, container_name=container_name)

        # 여러 파일 업로드 후 알림 메시지 한 번만 표시
        if result:
            msg_box = QMessageBox(QMessageBox.Information, "알림", f"{len(result)}개의 파일이 업로드되었습니다.")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.button(QMessageBox.Ok).setShortcut(Qt.Key_Return)
            msg_box.exec_()

    def download_files(self, list_widget, account, selected_items):
        """선택한 파일을 다운로드합니다."""
        logging.debug(f"선택한 파일 다운로드 시도. 계정: {account['account_name']}")
        if not selected_items:
            QMessageBox.information(list_widget, "알림", "다운로드할 파일을 선택하세요.")
            return

        # 다운로드할 경로 선택 (공통 경로 선택)
        save_directory = QFileDialog.getExistingDirectory(list_widget, "저장할 디렉토리 선택")
        if not save_directory:
            return  # 저장 경로를 선택하지 않은 경우

        for item in selected_items:
            file_path = item.text()

            if file_path.startswith("=====") or "[오류]" in file_path:
                continue

            try:
                container, blob_path = file_path.split("/", 1)
                container_client = account['client'].get_container_client(container)
                blob_client = container_client.get_blob_client(blob_path)

                save_path = os.path.join(save_directory, os.path.basename(blob_path))

                with open(save_path, "wb") as file:
                    data = blob_client.download_blob()
                    file.write(data.readall())

                logging.info(f"다운로드 성공: {blob_path} -> {save_path}")
            except Exception as e:
                logging.error(f"다운로드 실패: {file_path}, 이유: {e}")
                QMessageBox.warning(list_widget, "오류", f"파일 다운로드 실패: {file_path}\n{e}")

        QMessageBox.information(list_widget, "알림", "선택한 파일이 다운로드되었습니다.")

    def update_refresh_interval(self):
        """refresh_interval 값을 업데이트하고 YAML에 저장합니다."""
        logging.debug("refresh_interval 업데이트 시도")
        try:
            new_interval = int(self.interval_input.text())
            if new_interval > 0:
                self.refresh_interval = new_interval
                self.config['refresh_interval'] = new_interval
                self.config_handler.save_config(self.config)
                self.interval_label.setText(f"현재 refresh_interval: {self.refresh_interval} 초")
                QMessageBox.information(self, "알림", f"refresh_interval이 {new_interval} 초로 업데이트되었습니다.")
                logging.info(f"refresh_interval이 {new_interval} 초로 업데이트되었습니다.")
            else:
                logging.warning("양수가 아닌 값이 입력됨")
                QMessageBox.warning(self, "오류", "양수를 입력하세요.")
        except ValueError:
            logging.error("유효한 정수가 입력되지 않음")
            QMessageBox.warning(self, "오류", "유효한 정수를 입력하세요.")

    def toggle_single_account_mode(self, event, account):
        """특정 계정만 표시하거나 전체 계정으로 복구"""
        logging.debug(f"toggle_single_account_mode 호출됨. account: {account['account_name']}")
        if self.single_account_mode == account:
            self.single_account_mode = None
            for label, _, _ in self.account_widgets:
                label.parentWidget().show()
        else:
            self.single_account_mode = account
            for label, _, acc in self.account_widgets:
                if acc == account:
                    label.parentWidget().show()
                else:
                    label.parentWidget().hide()

    def toggle_layout_orientation(self):
        """가로/세로 레이아웃 변경"""
        logging.debug("레이아웃 방향 변경 시도")
        if self.layout_orientation == Qt.Vertical:
            self.layout_orientation = Qt.Horizontal
            self.layout_toggle_button.setText("세로로 변경")
        else:
            self.layout_orientation = Qt.Vertical
            self.layout_toggle_button.setText("가로로 변경")

        self.account_splitter.setOrientation(self.layout_orientation)

    def start_monitoring(self):
        """블랍 모니터링을 시작합니다."""
        logging.debug("블랍 모니터링 시작")
        self.update_blobs()
        self.monitoring_thread = threading.Thread(target=self.monitor_blobs, daemon=True)
        self.monitoring_thread.start()

    def monitor_blobs(self):
        """설정된 간격으로 블랍을 업데이트합니다."""
        while True:
            time.sleep(self.refresh_interval)
            logging.debug("모니터링 중 블랍 업데이트 호출")
            self.update_blobs()

    def update_blobs(self):
        """모든 계정과 컨테이너의 블랍 목록을 업데이트합니다."""
        logging.debug("update_blobs 함수 호출됨")
        for i, (label, list_widget, account) in enumerate(self.account_widgets):
            if self.single_account_mode and self.single_account_mode != account:
                continue
            list_widget.clear()
            self.blob_handler.update_blobs(account, list_widget)

    def select_all_files(self, list_widget):
        """컨테이너명을 제외하고 파일만 선택합니다."""
        for index in range(list_widget.count()):
            item = list_widget.item(index)
            if not item.text().startswith("=====") and "파일이 없습니다" not in item.text():
                item.setSelected(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = BlobMonitor()
    sys.exit(app.exec_())
