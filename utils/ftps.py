import os
import glob
from datetime import datetime
from ftplib import FTP_TLS

FTPS_HOST = os.getenv("FTPS_HOST")
FTPS_PORT = int(os.getenv("FTPS_PORT"))
FTPS_USER = os.getenv("FTPS_USER")
FTPS_PASSWORD = os.getenv("FTPS_PASSWORD")

FTPS_REPLAY_FILE_PATH = os.getenv("FTPS_REPLAY_FILE_PATH")
DOWNLOADED_REPLAY_FILE_PATH = os.getenv("DOWNLOADED_REPLAY_FILE_PATH")
FORTNITE_REPLAY_FILE_PATH = os.getenv("FORTNITE_REPLAY_FILE_PATH")

def connect():
    ftps = FTP_TLS()
    ftps.connect(FTPS_HOST, FTPS_PORT)
    ftps.login(user=FTPS_USER, passwd = FTPS_PASSWORD)
    return ftps


def download_file(ftps):
    ftps.cwd(FTPS_REPLAY_FILE_PATH)

    list_of_replay_files = list(ftps.mlsd())
    list_of_replay_files.sort(key = lambda replay: replay[1]['modify'], reverse = True)
    latest_replay_file = list_of_replay_files[0][0]

    saved_replay_file = open(DOWNLOADED_REPLAY_FILE_PATH + latest_replay_file, 'wb')
    ftps.retrbinary('RETR ' + latest_replay_file, saved_replay_file.write, 1024)

    delete_file(ftps, latest_replay_file)
    ftps.quit()
    saved_replay_file.close()

    return saved_replay_file


def upload_file(ftps, file_name):     
    try:
        new_file_name = "newest_replay.replay"
        with open(file_name, 'rb') as file:
            print(FTPS_REPLAY_FILE_PATH)
            ftps.cwd("/replays/")
            print('Uploading ' + file_name + "...")
            ftps.storbinary(f"STOR {new_file_name}", file)
            ftps.quit()
            ftps.close()
            file.close()
            print('Upload finished.')

    except:
       print("Error uploading file: " + file_name)


def delete_file(ftps, latest_replay_file):
    ftps.delete(FTPS_REPLAY_FILE_PATH + latest_replay_file)


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