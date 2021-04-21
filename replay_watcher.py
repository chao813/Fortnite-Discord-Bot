from dotenv import load_dotenv
load_dotenv()

import time 
import os
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from tkinter import *
import tkinter.messagebox as messagebox

import clients.replays as replays
import requests

FORTNITE_REPLAY_FILE_PATH = os.getenv("FORTNITE_REPLAY_FILE_PATH")
file_list = []


def create_empty_file():  
    path = FORTNITE_REPLAY_FILE_PATH
    today = datetime.now().strftime("%Y.%m.%d-%H.%M.%S")
    file_name = today + '_temp.txt'
    
    try:
        with open(os.path.join(path, file_name), 'w') as fp:
            return f"Successfully created file: {file_name}"
    except Exception as e:
        return f"Error creating file: {file_name}" 
        print(str(e))


textbox = None
def insert_watcher_event_message(message):   
    global textbox
    print(textbox)
    print(message)
    textbox.insert(END, message)


class Watcher():
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
            print(f"Received created event - {event.src_path}.")
            file_list.append(event.src_path)
            if len(file_list) > 2:
                file_list.pop(0)
            if len(file_list) == 2:
                # TODO: get rid of ftps, parse replay and generate body for POST
                eliminated_me_dict, eliminated_by_me_dict = replays.process_replays(file_list[0])
                body = {
                    "eliminated_me": eliminated_me_dict,
                    "eliminated_by_me": eliminated_by_me_dict
                }
                r = requests.post("http://localhost:5000/api/replay/elims", json = body)
 
            
        elif event.event_type == 'modified':
            # Taken any action here when a file is modified.
            print(f"Received modified event - {event.src_path}.")
            message = f"Received modified event - {event.src_path}."


def create_gui():
    window = Tk()
    window.title("Fortnite Replay Watcher")
    window.geometry('400x400')
    
    global textbox
    textbox = Text(window)
    textbox.pack(side=LEFT)
    scrollbar = Scrollbar(window)
    scrollbar.pack(side=RIGHT)

    #for i in range(100):
    #    textbox.insert(END, f"This is an example line {i}\n")

    textbox.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=textbox.yview)

    done_button = Button(window,text="Done Playing", command=done_button_clicked)
    done_button.place(relx=0.5, rely=1.0, anchor=S)

    return window

def done_button_clicked():
    message = create_empty_file()
    messagebox.showinfo('Done Playing', message)


if __name__ == '__main__':
    window = create_gui()
    window.mainloop()
    
    w = Watcher() 
    w.run()

    #eliminated_me_dict, eliminated_by_me_dict = replays.process_replays("/Users/yuanchao/Documents/Discord-Bot/Fortnite-Tracker-Bot/replays/UnsavedReplay-2021.04.14-01.06.45.replay")
    #body = {
    #    "eliminated_me": eliminated_me_dict,
    #    "eliminated_by_me": eliminated_by_me_dict
    #}
    #r = requests.post("http://localhost:5000/api/replay/elims", json = body)
    #print(r.text)
    