import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QProgressBar, QFileDialog
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QColor

from pytube import YouTube, Playlist

class DownloadThread(QThread):
    download_complete = pyqtSignal(str, int)

    def __init__(self, url, video_directory, parent=None):
        super(DownloadThread, self).__init__(parent)
        self.url = url
        self.video_directory = video_directory

    def run(self):
        try:
            if "playlist" in self.url.lower():
                playlist = Playlist(self.url)
                total_videos = len(playlist.video_urls)
                for index, video_url in enumerate(playlist.video_urls):
                    self.download_video(video_url)
                    self.download_complete.emit(video_url, int((index + 1) / total_videos * 100))
            else:
                self.download_video(self.url)
        except Exception as e:
            # Handle exceptions
            print(f"Error downloading video(s): {str(e)}")

    def download_video(self, video_url):
        try:
            yt = YouTube(video_url)
            video_stream = yt.streams.filter(file_extension="mp4", resolution="720p", progressive=True).first()

            if video_stream is not None:
                new_video_name = video_stream.title.lower().replace(' ', '') + '.mp4'
                video_file_path = os.path.join(self.video_directory, new_video_name)

                video_stream.download(self.video_directory)

                # Emit signal to indicate download completion
                self.download_complete.emit(new_video_name, 100)
            else:
                # Video stream is not available
                print("Error downloading video: Video stream is not available.")
        except Exception as e:
            # Print the exception traceback for debugging
            import traceback
            traceback.print_exc()
            print(f"Error downloading video: {str(e)}")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('YouTube Downloader')
        self.setGeometry(300, 300, 600, 300)  # Larger window size

        # Set background color
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor(240, 240, 240))  # Light gray background
        self.setPalette(p)

        self.playlist_url_label = QLabel('Playlist URL:')
        self.playlist_url_input = QLineEdit(self)
        self.playlist_directory = QLineEdit(self)
        self.select_url_button = QPushButton('Select Download Directory', self)
        self.start_download_button = QPushButton('Start Download Playlist', self)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(10, 220, 580, 20)  # Adjusted progress bar size

        vbox = QVBoxLayout()
        vbox.addWidget(self.playlist_url_label)
        vbox.addWidget(self.playlist_url_input)
        vbox.addWidget(self.playlist_directory)
        vbox.addWidget(self.select_url_button)
        vbox.addWidget(self.start_download_button)
        vbox.addWidget(self.progress_bar)

        self.setLayout(vbox)

        # Set style for buttons
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; /* Green */
                color: white;
                border: none;
                padding: 10px 15px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 5px;
            }

            QPushButton:hover {
                background-color: #45a049; /* Darker Green */
            }
        """)

        self.select_url_button.clicked.connect(self.select_directory)
        self.start_download_button.clicked.connect(self.start_download)

    def select_directory(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        video_directory = QFileDialog.getExistingDirectory(self, "Select Download Directory", options=options)
        print(video_directory)
        if video_directory:
            self.playlist_directory.setText(video_directory)

    def start_download(self):
        playlist_url = self.playlist_url_input.text()
        video_directory = self.playlist_directory.text()

        self.download_thread = DownloadThread(playlist_url, video_directory)
        self.download_thread.download_complete.connect(self.update_progress)
        self.download_thread.start()

    def update_progress(self, video_name, progress):
        print(f"Downloaded: {video_name}, Progress: {progress}%")
        self.progress_bar.setValue(progress)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
