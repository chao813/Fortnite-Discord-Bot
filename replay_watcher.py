from dotenv import load_dotenv
load_dotenv()

import time
import os

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import utils.ftps as ftps

FORTNITE_REPLAY_FILE_PATH = os.getenv("FORTNITE_REPLAY_FILE_PATH")
file_list = []

class Watcher:
    DIRECTORY_TO_WATCH = FORTNITE_REPLAY_FILE_PATH

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except:
            self.observer.stop()
            print("Error")

        self.observer.join()


class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            print("Received created event - %s." % event.src_path)
            file_list.append(event.src_path)
            if len(file_list) > 2:
                file_list.pop(0)
            if len(file_list) == 2:
                connected_ftps = ftps.connect_to_ftp()
                ftps.upload_file_to_ftp(connected_ftps, file_list[0])

        elif event.event_type == 'modified':
            # Taken any action here when a file is modified.
            print("Received modified event - %s." % event.src_path)
            #connected_ftps = ftps.connect_to_ftp()
            #ftps.upload_file_to_ftp(connected_ftps, event.src_path)
            



if __name__ == '__main__':
    w = Watcher()
    w.run()

