import ast
import os

from ray import Reader


SQUAD_PLAYERS_GUID_DICT = ast.literal_eval(str(os.getenv("SQUAD_PLAYERS_GUID_DICT")))
REPLAY_FILE_PATH = os.getenv("REPLAY_FILE_PATH")


def process_replays(replay_file):
    """ Process replays to return elimination dicts """
    eliminated_me_dict = {}
    eliminated_by_me_dict = {}

    if not replay_file.endswith(".replay"):
        return eliminated_me_dict, eliminated_by_me_dict

    try:
        with Reader(replay_file) as replay:
            eliminated_me_dict = _generate_eliminations_dict(
                replay.eliminations,
                _eliminated_me)
            eliminated_by_me_dict = _generate_eliminations_dict(
                replay.eliminations,
                _eliminated_by_me)
    except (FileNotFoundError, OSError) as e:
        print(f"Error reading replay file: {e}")
    except Exception as e:
        print(f"Error processing replay file data: {e}")

    return eliminated_me_dict, eliminated_by_me_dict


def _generate_eliminations_dict(eliminations, who_elim_who_func):
    """ Generate eliminations dict """
    eliminations_dict = {}

    for elim in eliminations:
        eliminations_dict = who_elim_who_func(elim, eliminations_dict)

    return eliminations_dict


def _eliminated_me(elim, eliminated_me_dict):
    """ Returns a dict of players who eliminated the caller """
    if elim.eliminated.guid in SQUAD_PLAYERS_GUID_DICT and \
       elim.eliminator.guid not in SQUAD_PLAYERS_GUID_DICT and \
       not elim.knocked:

        squad_player_name = SQUAD_PLAYERS_GUID_DICT[elim.eliminated.guid]

        if elim.eliminator.guid in eliminated_me_dict:
            eliminated_me_dict[elim.eliminator.guid].append(squad_player_name)
        else:
            eliminated_me_dict[elim.eliminator.guid] = [squad_player_name]

    return eliminated_me_dict


def _eliminated_by_me(elim, eliminated_by_me_dict):
    """ Returns a dict of players eliminated by the caller """
    if elim.eliminator.guid in SQUAD_PLAYERS_GUID_DICT and \
       elim.eliminated.guid not in SQUAD_PLAYERS_GUID_DICT and \
       not elim.knocked:

        squad_player_name = SQUAD_PLAYERS_GUID_DICT[elim.eliminator.guid]

        if squad_player_name in eliminated_by_me_dict:
            eliminated_by_me_dict[squad_player_name].append(elim.eliminated.guid)
        else:
            eliminated_by_me_dict[squad_player_name] = [elim.eliminated.guid]

    return eliminated_by_me_dict
