from dotenv import load_dotenv
load_dotenv()

import time
import os
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from tkinter import *

import clients.replays as replays
import requests


FORTNITE_REPLAY_FILE_PATH = os.getenv("FORTNITE_REPLAY_FILE_PATH")
FORTNITE_REPLAY_ELIM_ENDPOINT = os.getenv("FORTNITE_REPLAY_ELIM_ENDPOINT")
FORTNITE_REPLAY_ELIM_API_TOKEN = os.getenv("FORTNITE_REPLAY_ELIM_API_TOKEN")

file_list = []


def create_empty_file():
    path = FORTNITE_REPLAY_FILE_PATH
    today = datetime.now().strftime("%Y.%m.%d-%H.%M.%S")
    file_name = f"{today}_fortnite_tracker_dummy.txt"

    try:
        with open(os.path.join(path, file_name), "w") as _:
            return f"Successfully created file: {file_name}"
    except Exception as e:
        return f"Error creating file: {file_name}"


textbox = None
def insert_watcher_event_message(message):
    global textbox
    textbox.configure(state="normal")
    textbox.insert(END, message)


class Watcher():
    DIRECTORY_TO_WATCH = FORTNITE_REPLAY_FILE_PATH

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        window = create_gui()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        window.mainloop()
        try:
            while True:
                time.sleep(1)
        except Exception as e:
            self.observer.stop()
            print(f"Watcher error: {e}")

        self.observer.join()


class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        textbox.configure(state="disabled")
        if event.is_directory:
            return None

        elif event.event_type == "created":
            # Take any action here when a file is first created.
            print(f"Received created event - {event.src_path}.")
            insert_watcher_event_message(f"CREATED - {event.src_path}. \n")
            file_list.append(event.src_path)
            if len(file_list) > 2:
                file_list.pop(0)
            if len(file_list) == 2:
                latest_replay_file = file_list[0]
                eliminated_me_dict, eliminated_by_me_dict = replays.process_replays(
                    latest_replay_file)

                r = Handler.update_discord_bot(eliminated_me_dict, eliminated_by_me_dict)

                if not eliminated_me_dict and not eliminated_by_me_dict and r.ok:
                    insert_watcher_event_message("POST - Empty dummy file.\n")
                else:
                    insert_watcher_event_message("POST - {r.json()}.\n")
        elif event.event_type == 'modified':
            # Taken any action here when a file is modified.
            print(f"Received modified event - {event.src_path}.")

    @staticmethod
    def update_discord_bot(eliminated_me_dict, eliminated_by_me_dict):
        body = {
            "eliminated_me": eliminated_me_dict,
            "eliminated_by_me": eliminated_by_me_dict
        }

        headers = {
            "API-TOKEN": FORTNITE_REPLAY_ELIM_API_TOKEN
        }

        return requests.post(
            FORTNITE_REPLAY_ELIM_ENDPOINT,
            json=body,
            headers=headers)


def create_gui():
    window = Tk()
    window.title("Fortnite Replay Watcher")
    window.geometry("400x400")

    label = Label(window, text="Log:", font=("TkDefaultFont", 16))
    label.place(anchor=NW, x=0,y=18)

    global textbox
    textbox = Text(window)
    textbox.pack(side=LEFT)
    scrollbar = Scrollbar(window)
    scrollbar.pack(side=RIGHT)

    textbox.config(yscrollcommand=scrollbar.set)
    textbox.configure(state='disabled')
    scrollbar.config(command=textbox.yview)

    done_button = Button(window,text="Done Playing", command=done_button_clicked)
    done_button.place(relx=0.4, rely=1.0, anchor=S)
    clear_button = Button(window, text="Clear Log", command=clear_button_clicked)
    clear_button.place(relx=0.65, rely=1.0, anchor=S)

    return window


def done_button_clicked():
    message = create_empty_file()


def clear_button_clicked():
    textbox.configure(state="normal")
    textbox.delete("1.0", END)
    textbox.configure(state="disabled")

if __name__ == "__main__":
    w = Watcher()
    w.run()
