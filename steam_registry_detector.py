""" @file obs_renamer.py
    @author Sean Duffie
    @brief aid tool for organizing and renaming OBS clips
    
    Features:
    - [ ] Add game name to the filename
    - [ ] Group Clips by month/year
    - [ ] Mark overlapping clips??
"""
import sys

if sys.platform == 'win32':
    import winreg
elif sys.platform == 'linux' or sys.platform == 'linux2':
    import os
    import re

def get_running_steam_game():
    """ Returns the process id of the currently running steam game.

    Returns:
        _type_: _description_
    """
    if sys.platform == 'win32':
        try:
            steam_key = winreg.OpenKey(
                key=winreg.HKEY_CURRENT_USER,
                sub_key=r"Software\Valve\Steam",
                reserved=0,
                access=winreg.KEY_READ
            )
            game_id, _ = winreg.QueryValueEx(steam_key, "RunningAppID")
            winreg.CloseKey(steam_key)

            if game_id:
                game_key = winreg.OpenKey(
                    key=winreg.HKEY_CURRENT_USER,
                    sub_key=f"Software\\Valve\\Steam\\Apps\\{game_id}",
                    reserved=0,
                    access=winreg.KEY_READ
                )
                _, game_name, _ = winreg.EnumValue(game_key, 2)
                winreg.CloseKey(game_key)

                return game_id, game_name
            else:
                return None, None
        except FileNotFoundError:
            print("FileNotFoundError")
            return None, None
    elif sys.platform == 'linux' or sys.platform == 'linux2':
        try:
            with open(os.path.expanduser("~/.steam/registry.vdf"), 'r', encoding="utf-8") as f:
                content = f.read()
                match = re.search(r'"RunningAppID"\s+"(\d+)"', content)
                if match:
                    return match.group(1), "TODO"
                else:
                    return None, None
        except FileNotFoundError:
            return None, None
    else:
        return None, None

if __name__ == "__main__":
    running_game_id, running_game_name = get_running_steam_game()
    if running_game_id:
        print(f"Running Steam Game ID: {running_game_id} ({running_game_name})")
    else:
        print("No Steam game is currently running.")
