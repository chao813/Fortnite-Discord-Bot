import ast
import os

from ray import Reader


SQUAD_PLAYERS_GUID_DICT = ast.literal_eval(str(os.getenv("SQUAD_PLAYERS_GUID_DICT")))
REPLAY_FILE_PATH = os.getenv("REPLAY_FILE_PATH")


def process_replays(replay_file):
    """ Process replays to return elimination dicts """
    eliminated_by_dict = {}
    eliminated_dict = {}

    if not replay_file.endswith(".replay"):
        return eliminated_by_dict, eliminated_dict

    try:
        with Reader(replay_file) as replay:
            eliminated_by_dict = _generate_eliminations_dict(
                replay.eliminations,
                _get_eliminated_by)
            eliminated_dict = _generate_eliminations_dict(
                replay.eliminations,
                _get_eliminated)
    except (FileNotFoundError, OSError) as e:
        print(f"Error reading replay file: {e}")
    except Exception as e:
        print(f"Error processing replay file data: {e}")

    return eliminated_by_dict, eliminated_dict


def _generate_eliminations_dict(eliminations, who_elim_who_func):
    """ Generate eliminations dict """
    eliminations_dict = {}

    for elim in eliminations:
        eliminations_dict = who_elim_who_func(elim, eliminations_dict)

    return eliminations_dict


def _get_eliminated_by(elim, eliminated_by_dict):
    """ Returns a dict of players who eliminated the caller """
    killer_guid = elim.eliminator.guid
    victim_guid = elim.eliminated.guid
    squad_player_name = SQUAD_PLAYERS_GUID_DICT[victim_guid]

    if _was_eliminated(elim.knocked) and \
       _is_squad_player(victim_guid) and \
       not _is_squad_player(killer_guid):

        if killer_guid in eliminated_by_dict:
            eliminated_by_dict[killer_guid].append(squad_player_name)
        else:
            eliminated_by_dict[killer_guid] = [squad_player_name]

    return eliminated_by_dict


def _get_eliminated(elim, eliminated_dict):
    """ Returns a dict of players eliminated by the caller """
    killer_guid = elim.eliminator.guid
    victim_guid = elim.eliminated.guid
    squad_player_name = SQUAD_PLAYERS_GUID_DICT[victim_guid]

    if _was_eliminated(elim.knocked) and \
       _is_squad_player(killer_guid) and \
       not _is_squad_player(victim_guid):

        if squad_player_name in eliminated_dict:
            eliminated_dict[squad_player_name].append(victim_guid)
        else:
            eliminated_dict[squad_player_name] = [victim_guid]

    return eliminated_dict


def _is_squad_player(player_guid):
    """ Player is a predefined squad player """
    return player_guid in SQUAD_PLAYERS_GUID_DICT


def _was_eliminated(knocked):
    """ Player was eliminated """
    return not knocked
