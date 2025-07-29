""" @file GameNamer.py
    @author Sean Duffie
    @brief OBS plugin

    Original Source: https://github.com/cr08/OBS-Recording-Renamer/tree/main
    - I modified this for my own personal use.
"""
import os
import os.path
import threading
import time
import urllib.request

import obspython as OBS  # pylint: disable=import-error
from steam_registry_detector import get_running_steam_game

# import pywinctl as pwc



class Data:
    """ Struct for holding Flags and Constants. """
    Delay = None
    Debug = False
    Replay_True = False
    RenameMode = None
    WindowCount = None
    ChannelName = None

# def debug(message: str):
#     """ Wrapper for print statement to reduce linting errors.

#     Args:
#         message (str): the message to be debugged.
#     """
#     if Data.Debug:
#         print(message)

def clean_filename(sourcestring: str,  removestring: str="\`/<>\:\"\\|?*"):
    """ Remove Invalid Characters from Filename.

    Args:
        sourcestring (str): The original filename.
        removestring (str): A list of chars to remove.

    Returns:
        str: Modified Filename string.
    """
    if sourcestring is None or sourcestring == "_":
        sourcestring = ""
    return ''.join([c for c in sourcestring if c not in removestring])

def rename_files(old_path, new_path):
    """ Rename the file. No actual decisions are made here.

    Args:
        old_path (str): Vanilla file name suggested.
        new_path (str): Modified Output File Name.
    """
    if Data.Debug:
        print("DEBUG: Renaming files")

    try:
        if Data.Debug:
            print("DEBUG: Old file path - " + old_path)
            print("DEBUG: New file path - " + new_path)
        os.rename(old_path, new_path)
        if Data.Debug:
            print("DEBUG: Recording renamed.")
    except OSError as e:
        print(f"ERROR: {e}")

def get_foreground_window():
    """ Uses the pywinctl package to get the current active window.

    Returns:
        str: Foreground window name
    """
    window_name = "TEMP"
    # window_name = "_" + pwc.getActiveWindowTitle()
    window_name = clean_filename(window_name)
    if Data.Debug:
        print("DEBUG: Current Foreground Window: \"" + window_name + "\"")
    return window_name

def get_steam_game():
    """ Uses registers to access Steam and see what game is currently running.

    Returns:
        str: Steam game name
    """
    game_name = str(get_running_steam_game()[1])
    game_name = clean_filename(game_name)
    # if "None" in game_name:
    #     game_name = "Non-Steam"
    if Data.Debug:
        print("DEBUG: Current Steam Game: \"", game_name, "\"")

    return game_name

def get_twitch_title():
    """ Uses the Twitch API to get the title of your twitch stream

    Returns:
        str: Twitch Title
    """
    twitch_streamtitle = urllib.request.urlopen(
        "https://decapi.me/twitch/title/" + str(Data.ChannelName)).read().decode("utf-8")
    twitch_game = urllib.request.urlopen(
        "https://decapi.me/twitch/game/" + str(Data.ChannelName)).read().decode("utf-8")
    title = "VOD_" + Data.ChannelName + "_" + str(twitch_game) + "_" + str(twitch_streamtitle)
    title = clean_filename(title)
    if Data.Debug:
        print("DEBUG: Twitch Mode: Channel - " + Data.ChannelName)
        print("DEBUG: Twitch Mode: Game - " + str(twitch_game.decode("utf-8")))
        print("DEBUG: Twitch Mode: Stream Title - " + str(twitch_streamtitle.decode("utf-8")))
        print("DEBUG: Title Addition - \"" + title + "\"")
    return title

def rename() -> None:
    """ Get most recent recording and handle the renaming process.

        - First, get the name of the most recent recording and parse it.
        - Then, wait for the remux to finish.
        - Delete the ".mkv" file.
        - Get the title of the desired application.
        - Finally, rename the ".mp4" file.

        All of this should be done on a separate thread to not block the main process.
        FIXME: Will this leave hanging threads if something is interrupted?
    """
    # Get and parse the most recent recording name.
    path = OBS.obs_frontend_get_last_recording()
    dirname = os.path.dirname(path)
    raw_file = os.path.basename(path)
    root_ext = os.path.splitext(raw_file)

    # Wait for the ".mp4" file to be created. (This doesn't mean the remux is finished).
    old_mp4 = os.path.join(dirname, root_ext[0] + ".mp4")
    check = 500
    while not os.path.exists(old_mp4):
        if not check:
            print("Error: The process hung for too long. Maybe the video was long?")
            break
        check -= 1

        if Data.Debug and check % 100 == 0:
            print("Waiting on remux...\tRemux: " + old_mp4 + "\tOriginal: " + path + "\n")

        time.sleep(.1)

    # Remove the original MKV. If a permission error occurs then the file is still being remuxxed.
    while os.path.exists(path):
        try:
            os.remove(path)
        except PermissionError:
            print("Waiting for the remux to finish...")
            time.sleep(.1)

    # Generate new title.
    title = "_"
    if Data.Debug:
        print("DEBUG: Recording session STOPPED...")

    if Data.RenameMode == 0:
        title += get_steam_game()

    elif Data.RenameMode == 1:
        title += get_twitch_title()

    elif Data.RenameMode == 2:
        title += get_foreground_window()

    else:
        title = ""
        if Data.Debug:
            print("DEBUG: The Rename mode you selected has not been implemented yet.")

    new_title = root_ext[0] + title + ".mp4"
    new_mp4 = os.path.join(dirname, new_title)

    # Rename the actual file.
    rename_files(old_mp4,new_mp4)
    # os.remove(old_mp4)

def on_event(event):
    """ 

    Args:
        event (_type_): _description_
    """
    if event == OBS.OBS_FRONTEND_EVENT_RECORDING_STOPPED:
        thread = threading.Thread(target=rename, name="OBSRenamer")
        thread.start()
        if Data.Debug:
            print("Rename thread started!")

    if event == OBS.OBS_FRONTEND_EVENT_REPLAY_BUFFER_SAVED:
        thread = threading.Thread(target=rename)
        thread.start()
        if Data.Debug:
            print("Rename thread started!")

    # if event == OBS.OBS_FRONTEND_EVENT_RECORDING_STARTED:
    #     if Data.Debug:
    #         print("DEBUG: Recording session started...")
    #     print("Triggered when the recording started. Window log cleaned and started.")
    #     with open(OBS.script_path()+'/WindowLog.txt', encoding='utf_8') as winlist:
    #         if os.path.exists(winlist):
    #             os.remove(winlist)
    #             print("DEBUG: WindowLog.txt file found. Deleting and starting clean log.")
    #         else:
    #             print("DEBUG: No WindowLog.txt file found. Ignoring.")

    # if event == OBS.OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTED:
    #     if Data.Debug:
    #         print("DEBUG: Replay Buffer Started")

    # if event == OBS.OBS_FRONTEND_EVENT_REPLAY_BUFFER_STOPPED:
    #     if Data.Debug:
    #         print("DEBUG: Replay Buffer Stopped")


def script_description():
    """ Called to display a string to the user in the Scripts Window.

    Returns:
        str: String to display to the user. Can use HTML.
    """
    description = """
        <center><h2>OBS-Rec-Rename</h2></center>
        <center><h3>Script to automatically rename recordings based on content.</h3></center>
        <center><h4>Click <a href=\"https://github.com/cr08/obs-rec-rename#readme\">here</a>
        for documentation.<hr>
    """
    return description


def script_load(settings):
    """ OBS API Event called when the script is first loaded. """
    OBS.obs_frontend_add_event_callback(on_event)


def script_properties():
    """ The OBS Options displayed in the Scripts Window.

    Returns:
        _type_: _description_
    """
    props = OBS.obs_properties_create()
    # period_p = OBS.obs_properties_add_int(
    #     props,"period","Time interval (s)", 5, 3600, 5)
    mode_p = OBS.obs_properties_add_list(
        props,"mode","Rename Mode",OBS.OBS_COMBO_TYPE_LIST,OBS.OBS_COMBO_FORMAT_INT)
    OBS.obs_property_list_add_int(
        mode_p,"Currently running Steam title", 0)
    OBS.obs_property_list_add_int(
        mode_p,"Twitch Stream title", 1)
    OBS.obs_property_list_add_int(
        mode_p, "Foreground Window Name", 2)
    # OBS.obs_property_list_add_int(
    #     mode_p, "Most active scene name", 3)
    # OBS.obs_property_list_add_int(
    #     mode_p, "Most active game or window capture source", 4)
    # OBS.obs_property_list_add_int(
    #     mode_p, "OBS Profile name", 5)
    # OBS.obs_property_list_add_int(
    #     mode_p, "OBS Scene Collection name", 6)

    # OBS.obs_properties_add_int(
    #     props,"windowcount", "Window count", 1, 99, 1)
    OBS.obs_properties_add_text(
        props,"twitch_channel","Twitch Channel",OBS.OBS_TEXT_DEFAULT)
    OBS.obs_properties_add_bool(
        props,"replay_true", "Rename Replays?")
    OBS.obs_properties_add_bool(
        props,"debug", "Enable Debug")

    return props


def script_update(settings):
    """ OBS API Event called when the script is updated. """
    Data.DelayOld = Data.Delay
    Data.Delay = 1000*OBS.obs_data_get_int(settings,"period") or 5000
    Data.Debug = OBS.obs_data_get_bool(settings,"debug") or False
    Data.Replay_True = OBS.obs_data_get_bool(settings,"replay_true") or False
    Data.WindowCount = OBS.obs_data_get_int(settings,"windowcount") or 1
    Data.RenameMode = OBS.obs_data_get_int(settings,"mode")
    Data.ChannelName = OBS.obs_data_get_string(settings, "twitch_channel")

    if Data.Debug:
        print("DEBUG: Script updating...")
        print("DEBUG: Interval - " + str(Data.Delay))
        print("DEBUG: Debug - " + str(Data.Debug))

        if Data.RenameMode == 0:
            print("DEBUG: RenameMode - Active Window(s) title - " + str(Data.RenameMode))
        elif Data.RenameMode == 1:
            print("DEBUG: RenameMode - Twitch Game/Stream title - " + str(Data.RenameMode))
            print("DEBUG: Twitch Channel - " + str(Data.ChannelName))
        elif Data.RenameMode == 2:
            print("DEBUG: RenameMode - Active Scene(s) - " + str(Data.RenameMode))
        elif Data.RenameMode == 3:
            print("DEBUG: RenameMode - Active Game/Window Capture Source(s) - " + str(Data.RenameMode))
        elif Data.RenameMode == 4:
            print("DEBUG: RenameMode - OBS Profile Name - " + str(Data.RenameMode))
        elif Data.RenameMode == 5:
            print("DEBUG: RenameMode - OBS Scene Collection Name - " + str(Data.RenameMode))
        print("DEBUG: Rename Replays - " + str(Data.Replay_True))

    if Data.Delay != Data.DelayOld:
        if Data.Debug:
            print("DEBUG: Time interval changed. Restarting timer_process.")

        # OBS.timer_remove(timer_process)
        # OBS.timer_add(timer_process, Data.Delay)

# def timer_process():
#     print("timer activated")
    # rename_files(Data.OutputDir)
    # get_foreground_window()
