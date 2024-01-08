import os
from email import errors

from PyQt5.QtMultimediaWidgets import QVideoWidget
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from PyQt5.QtWidgets import (
    QApplication, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QListWidget,
    QListWidgetItem, QMessageBox, QHBoxLayout
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayerControl, QMediaPlayer
from PyQt5.QtGui import QIcon

# Set Wayland as the platform (optional)
os.environ["QT_QPA_PLATFORM"] = "wayland"

# Set the appropriate scope
SCOPES = ["https://www.googleapis.com/auth/drive"]

class GoogleDriveFolderCreator(QWidget):
    def __init__(self):
        super().__init__()

        self.credentials = self.load_credentials()
        self.drive_service = build("drive", "v3", credentials=self.credentials)

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Google Drive Folder Creator")
        self.setGeometry(100, 100, 800, 600)  # Set initial window size

        self.label = QLabel("Enter Folder Name:")
        self.folder_name_input = QLineEdit(self)
        self.submit_button = QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.create_folder)

        self.success_label = QLabel(self)
        self.success_label.setStyleSheet("color: green;")

        self.folder_list_widget = QListWidget(self)
        self.refresh_button = QPushButton("Refresh Folder List", self)
        self.refresh_button.clicked.connect(self.refresh_folder_list)

        self.delete_button = QPushButton("Delete Selected Folder", self)
        self.delete_button.clicked.connect(self.delete_selected_folder)

        self.video_list_widget = QListWidget(self)
        self.fetch_videos_button = QPushButton("Fetch Videos", self)
        self.fetch_videos_button.clicked.connect(self.fetch_videos)

        self.media_player = QMediaPlayer(self)
        self.video_widget = QVideoWidget(self)

        # Add controls for video playback
        self.play_button = QPushButton("Play", self)
        self.play_button.clicked.connect(self.play_video)

        self.pause_button = QPushButton("Pause", self)
        self.pause_button.clicked.connect(self.pause_video)

        self.stop_button = QPushButton("Stop", self)
        self.stop_button.clicked.connect(self.stop_video)

        self.skip_forward_button = QPushButton("Skip Forward (10s)", self)
        self.skip_forward_button.clicked.connect(self.skip_forward)

        self.rewind_button = QPushButton("Rewind (10s)", self)
        self.rewind_button.clicked.connect(self.rewind)

        self.fullscreen_button = QPushButton("Fullscreen", self)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.folder_name_input)
        layout.addWidget(self.submit_button)
        layout.addWidget(self.success_label)
        layout.addWidget(self.folder_list_widget)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.video_list_widget)
        layout.addWidget(self.fetch_videos_button)
        layout.addWidget(self.video_widget)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.skip_forward_button)
        controls_layout.addWidget(self.rewind_button)
        controls_layout.addWidget(self.fullscreen_button)
        layout.addLayout(controls_layout)

        self.setLayout(layout)

        self.folder_list_widget.itemDoubleClicked.connect(self.fetch_videos)

    def load_credentials(self):
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        return creds

    def create_folder(self):
        folder_name = self.folder_name_input.text()
        if folder_name:
            try:
                folder_metadata = {
                    "name": folder_name,
                    "mimeType": "application/vnd.google-apps.folder",
                }
                folder = self.drive_service.files().create(body=folder_metadata).execute()
                success_message = f"Folder '{folder_name}' created in Google Drive with ID: {folder['id']}"
                print(success_message)
                self.success_label.setText(success_message)
                self.refresh_folder_list()
            except HttpError as error:
                if "insufficientPermissions" in str(error):
                    print("Error: Insufficient permissions. Make sure the scope is correct.")
                    self.success_label.setText("Error: Insufficient permissions.")
                else:
                    error_message = f"An error occurred: {error}"
                    print(error_message)
                    self.success_label.setText(error_message)

    def refresh_folder_list(self):
        try:
            folders = self.get_all_folders()
            self.populate_folder_list(folders)
        except HttpError as error:
            print(f"An error occurred while fetching folders: {error}")

    def get_all_folders(self):
        folders = []
        page_token = None
        while True:
            try:
                response = self.drive_service.files().list(
                    q="mimeType='application/vnd.google-apps.folder'",
                    spaces="drive",
                    fields="nextPageToken, files(id, name)",
                    pageToken=page_token,
                ).execute()
                folders.extend(response.get("files", []))
                page_token = response.get("nextPageToken", None)
                if page_token is None:
                    break
            except errors.HttpError as error:
                print(f"An error occurred while listing folders: {error}")
                break
        return folders

    def populate_folder_list(self, folders):
        self.folder_list_widget.clear()
        for folder in folders:
            folder_name = folder.get("name")
            folder_id = folder.get("id")
            item = QListWidgetItem(f"{folder_name} (ID: {folder_id})", self.folder_list_widget)
            item.setData(Qt.UserRole, folder_id)

    def delete_selected_folder(self):
        selected_item = self.folder_list_widget.currentItem()
        if selected_item:
            folder_id = selected_item.data(Qt.UserRole)
            confirm_dialog = QMessageBox.question(
                self,
                "Delete Folder",
                f"Do you want to delete the folder with ID: {folder_id}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if confirm_dialog == QMessageBox.Yes:
                try:
                    self.drive_service.files().delete(fileId=folder_id).execute()
                    print(f"Folder with ID {folder_id} deleted successfully.")
                    self.refresh_folder_list()
                except HttpError as error:
                    print(f"An error occurred while deleting folder: {error}")
        else:
            QMessageBox.warning(self, "No Folder Selected", "Please select a folder to delete.")

    def fetch_videos(self):
        selected_item = self.folder_list_widget.currentItem()
        if selected_item:
            folder_id = selected_item.data(Qt.UserRole)
            try:
                videos = self.get_videos_from_folder(folder_id)
                self.populate_video_list(videos)
            except HttpError as error:
                print(f"An error occurred while fetching videos: {error}")

    def get_videos_from_folder(self, folder_id):
        videos = []
        try:
            response = self.drive_service.files().list(
                q=f"'{folder_id}' in parents and mimeType contains 'video/'",
                spaces="drive",
                fields="nextPageToken, files(id, name)",
            ).execute()
            videos.extend(response.get("files", []))
            print("Response from Google Drive API:", response)
        except errors.HttpError as error:
            print(f"An error occurred while listing videos: {error}")
        return videos

    def populate_video_list(self, videos):
        self.video_list_widget.clear()
        for video in videos:
            video_name = video.get("name")
            video_id = video.get("id")
            item = QListWidgetItem(f"{video_name} (ID: {video_id})", self.video_list_widget)
            item.setData(Qt.UserRole, video_id)

    def play_video(self):
        selected_item = self.video_list_widget.currentItem()
        if selected_item:
            video_id = selected_item.data(Qt.UserRole)
            video_url = f"https://drive.google.com/uc?id={video_id}"

            media_content = QMediaContent(QUrl.fromLocalFile(video_url))
            self.media_player.setMedia(media_content)
            self.media_player.setVideoOutput(self.video_widget)
            self.media_player.play()

    def pause_video(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()

    def stop_video(self):
        self.media_player.stop()

    def skip_forward(self):
        position = self.media_player.position() + 10000  # 10 seconds forward
        self.media_player.setPosition(position)

    def rewind(self):
        position = self.media_player.position() - 10000  # 10 seconds rewind
        self.media_player.setPosition(position)

    def toggle_fullscreen(self):
        if self.video_widget.isFullScreen():
            self.video_widget.setFullScreen(False)
        else:
            self.video_widget.setFullScreen(True)

if __name__ == "__main__":
    app = QApplication([])
    app.setWindowIcon(QIcon("icon.png"))  # Replace "icon.png" with your icon file
    window = GoogleDriveFolderCreator()
    window.show()
    app.exec_()
