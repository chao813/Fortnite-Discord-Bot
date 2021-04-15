import os
import ast
import glob
from ray import Reader

SQUAD_PLAYERS_GUID_DICT = ast.literal_eval(str(os.getenv("SQUAD_PLAYERS_GUID_DICT")))
REPLAY_FILE_PATH = os.getenv("REPLAY_FILE_PATH")

def eliminated_me(elim, eliminated_me_dict):
    if elim.eliminated.guid in SQUAD_PLAYERS_GUID_DICT and not elim.knocked:
        if elim.eliminator.guid in eliminated_me_dict:
            eliminated_me_dict[elim.eliminator.guid].append(SQUAD_PLAYERS_GUID_DICT[elim.eliminated.guid])
        else:
            eliminated_me_dict[elim.eliminator.guid] = [SQUAD_PLAYERS_GUID_DICT[elim.eliminated.guid]]
    return eliminated_me_dict

def eliminated_by_me(elim, eliminated_by_me_dict):
    if elim.eliminator.guid in SQUAD_PLAYERS_GUID_DICT and not elim.knocked:
        if elim.eliminated.guid in eliminated_by_me_dict:
            eliminated_by_me_dict[SQUAD_PLAYERS_GUID_DICT[elim.eliminator.guid]].append(elim.eliminated.guid)
        else:
            eliminated_by_me_dict[SQUAD_PLAYERS_GUID_DICT[elim.eliminator.guid]] = [elim.eliminated.guid]
    return eliminated_by_me_dict

def generate_eliminations_dict(eliminations, who_elim_who_func):
    eliminations_dict = {}

    for elim in eliminations:
        eliminations_dict = who_elim_who_func(elim, eliminations_dict)

    return eliminations_dict
                    

def process_replays(): 
    try:
        list_of_replay_files = glob.glob(REPLAY_FILE_PATH + "*.replay") 
        latest_replay_file = max(list_of_replay_files, key=os.path.getctime)
        with Reader(latest_replay_file) as replay:
            eliminated_me_dict = generate_eliminations_dict(replay.eliminations, eliminated_me)
            eliminated_by_me_dict = generate_eliminations_dict(replay.eliminations, eliminated_by_me)
            return eliminated_me_dict, eliminated_by_me_dict
    except:
        print("No replay file found")
        return None, None