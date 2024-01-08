import os
import json
from pytube import YouTube
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QProgressBar
from PyQt5.QtCore import QThread, pyqtSignal, QObject


class DownloadThread(QThread):
    download_complete = pyqtSignal(str)

    def __init__(self, song_name, video_url, download_directory):
        super(DownloadThread, self).__init__()
        self.song_name = song_name
        self.video_url = video_url
        self.download_directory = download_directory

    def run(self):
        try:
            yt = YouTube(self.video_url)
            video_stream = yt.streams.filter(file_extension="mp4", progressive=True).first()

            if video_stream is not None:
                new_video_name = video_stream.title.lower().replace(' ', '') + '.mp4'
                video_file_path = os.path.join(self.download_directory, new_video_name)

                # Download video without showing progress (for simplicity)
                video_stream.download(self.download_directory)

                # Emit signal to indicate download completion
                self.download_complete.emit(new_video_name)
            else:
                # Video stream is not available
                print(f"Error downloading video '{self.song_name}': Video stream is not available.")
        except Exception as e:
            # Print the exception traceback for debugging
            import traceback
            traceback.print_exc()
            print(f"Error downloading video '{self.song_name}': {str(e)}")


class DownloadManager(QObject):
    download_complete = pyqtSignal(str)
    progress_update = pyqtSignal(int, int)
    status_update = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.download_threads = []
        self.total_videos = 0
        self.downloaded_videos = 0
        self.json_file_path = ""
        self.download_directory = ""

    def download_videos(self):
        try:
            with open(self.json_file_path, 'r') as file:
                data = json.load(file)
                self.total_videos = len(data)

            for entry in data:
                song_name = entry.get("name")
                video_url = entry.get("url")

                download_thread = DownloadThread(song_name, video_url, self.download_directory)
                download_thread.download_complete.connect(self.handle_download_complete)
                download_thread.start()
                self.download_threads.append(download_thread)

        except Exception as e:
            # Print the exception traceback for debugging
            import traceback
            traceback.print_exc()
            error_text = f"Error reading JSON file: {str(e)}"
            print(error_text)

    def handle_download_complete(self, video_name):
        self.downloaded_videos += 1
        self.download_complete.emit(video_name)

        # Update progress
        progress_percentage = int(self.downloaded_videos / self.total_videos * 100)
        self.progress_update.emit(self.downloaded_videos, progress_percentage)

        # Check if all videos are downloaded successfully
        if self.downloaded_videos == self.total_videos:
            self.status_update.emit("All videos downloaded successfully from the JSON file.")


class UI(QWidget):
    def __init__(self):
        super().__init__()

        self.download_manager = DownloadManager()

        self.layout = QVBoxLayout()

        self.select_json_button = QPushButton('Select JSON File')
        self.select_directory_button = QPushButton('Select Download Directory')
        self.download_button = QPushButton('Download Videos')

        self.result_label = QLabel()
        self.progress_label = QLabel()
        self.status_label = QLabel()
        self.progress_bar = QProgressBar()

        self.layout.addWidget(self.select_json_button)
        self.layout.addWidget(self.select_directory_button)
        self.layout.addWidget(self.download_button)
        self.layout.addWidget(self.result_label)
        self.layout.addWidget(self.progress_label)
        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.progress_bar)

        self.setLayout(self.layout)
        self.setGeometry(300, 300, 400, 200)
        self.setWindowTitle('YouTube Video Downloader')

        self.select_json_button.clicked.connect(self.select_json_file)
        self.select_directory_button.clicked.connect(self.select_download_directory)
        self.download_button.clicked.connect(self.download_videos)

        self.download_manager.download_complete.connect(self.update_result_label)
        self.download_manager.progress_update.connect(self.update_progress_label)
        self.download_manager.status_update.connect(self.update_status_label)

    def select_json_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.download_manager.json_file_path, _ = QFileDialog.getOpenFileName(
            self, "Select JSON File", "", "JSON Files (*.json);;All Files (*)", options=options
        )

    def select_download_directory(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.download_manager.download_directory = QFileDialog.getExistingDirectory(
            self, "Select Download Directory", options=options
        )

    def download_videos(self):
        # Check if both JSON file and download directory are selected
        if not self.download_manager.json_file_path or not self.download_manager.download_directory:
            print("Error: JSON file or download directory not selected.")
            return

        # Reset progress bar before starting new downloads
        self.progress_bar.reset()

        # Reset counters
        self.download_manager.total_videos = 0
        self.download_manager.downloaded_videos = 0

        # Download videos using the selected JSON file and download directory
        self.download_manager.download_videos()

    def update_result_label(self, video_name):
        print(f"Video '{video_name}' downloaded successfully!")

    def update_progress_label(self, downloaded_videos, progress_percentage):
        # Update the progress bar value based on the number of downloaded videos
        self.progress_bar.setValue(progress_percentage)

        # Update the progress label
        self.progress_label.setText(f"Download Progress: {progress_percentage}%")

    def update_status_label(self, status_message):
        self.status_label.setText(status_message)


if __name__ == '__main__':
    app = QApplication([])

    ui = UI()
    ui.show()

    app.exec_()
