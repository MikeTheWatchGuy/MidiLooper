import os
import logging
import PySimpleGUI as sg
from MvidMido import *


# ---===--- Player GUI commands --- #
# NOTE these are shared between MIDI-Video Player and MIDI-Player
PLAYER_COMMAND_PAUSE = 1
PLAYER_COMMAND_EXIT = 69
PLAYER_COMMAND_NONE = 2
PLAYER_COMMAND_NEXT = 3
PLAYER_COMMAND_CANCEL = 4
PLAYER_COMMAND_REWIND = 5
PLAYER_COMMAND_FAST_FORWARD = 6
PLAYER_COMMAND_SET_A = 7
PLAYER_COMMAND_SET_B = 8
PLAYER_COMMAND_CLEAR_LOOP = 9
PLAYER_COMMAND_RESTART_SONG = 10
PLAYER_COMMAND_SLIDER = 11
PLAYER_COMMAND_PLAY = 6969

# ---===--- Recorder GUI commands --- #
RECORDER_COMMAND_EXIT = 69
RECORDER_COMMAND_NONE = 2
RECORDER_COMMAND_START = 3
RECORDER_COMMAND_STOP = 4
RECORDER_COMMAND_SAVE = 5
RECORDER_COMMAND_CANCEL = 6
RECORDER_COMMAND_PAUSE = 7
RecorderLookup = {'EXIT':RECORDER_COMMAND_EXIT, 'Stop': RECORDER_COMMAND_STOP, 'Start': RECORDER_COMMAND_START, 'Save':RECORDER_COMMAND_SAVE, 'Pause':RECORDER_COMMAND_PAUSE}

logging.basicConfig(level=logging.ERROR)

# logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.ERROR)

def no_func(*args):
    return



# ---------------------------------------------------------------------- #
#    MIDIVideoFile         CLASS                                         #
#       Holds the current item being played or list of items playing     #
# ---------------------------------------------------------------------- #
class MIDIVideoFile():
    def __init__(self, Link=None, Filename=None, FolderPlaylist=None, YouTubeLink=None, YouTubePlaylist=None, Looping=False):
        self.Link = Link
        self.Filename = Filename
        self.IsLink = (Link != None)
        self.FolderPlaylist = FolderPlaylist
        self.YouTubeLink = YouTubeLink
        self.YouTubePlaylist = YouTubePlaylist
        self.Looping = Looping

# ---------------------------------------------------------------------- #
#    PlayerGUI             CLASS                                         #
# ---------------------------------------------------------------------- #
class PlayerGUI():
    '''
    Class implementing GUI for both initial screen but the player itself
    '''
    # Used to tell how much longer or shorter to wait between notes. Large values imply waiting longer
    TempoDisplayvalues = (-6,-5,-4,-3,-2,-1,0,1,2,3,4,5,6)
    TempoTable =( 4.0, 3.0,2.0,1.8,1.6, 1.4, 1.2, 1.0, .9, .8, .7, .6, .5, .4, .3)
    VolumeAdjustmentTable =(.1, .3, .4, .5, .6, .7, .8, .9, .95, 1.1, 1.2, 1.3, 1.4)
    VolumeSettings = (-6,-5,-4,-3,-2,-1,0,1,2,3,4,5,6)
    ABMarkerAdjustments = [i for i in range(-20,21)]

    def __init__(self):
        self.OffsetDisplayTextElement = None
        self.window = None
        self.TextElem = None
        self.LastTempo = 1.0
        self.Tempo = 1.0
        self.Name = ''
        self.PortList = mido.get_output_names()        # use to get the list of midi ports
        # uncomment out line to reverse the order of midi-ports in the GUI (set the default to your choosing)
        self.PortList = self.PortList[::-1]            # reverse the list so the last one is first
        self.Volume = 0
        self.LoopRegion = False
        self.RemapChannels = True
        self.PlayOnlyChannel0 = False
        self.AMarkerAdjustment = 0
        self.BMarkerAdjustment = 0
        self.AMarkerTextElem = None
        self.BMarkerTextElem = None
        self.pedal_hack = True
        self.velocity_hack = True

    # ---------------------------------------------------------------------- #
    #  PlayerChooseSongGUI                                                   #
    #   Show a GUI get to the file to playback                               #
    # ---------------------------------------------------------------------- #
    def PlayerChooseSongGUI(self):
        # Build list of movies in the default path for pull-downlist
        default_port = 0
        for item in self.PortList:
            if 'yamaha' in item.lower():
                default_port = item
                print(f'Auto selecting port {default_port}')
                break
        # ---------------------- DEFINION OF CHOOSE WHAT TO PLAY GUI ----------------------------
        layout = [[sg.Text('MIDI Looper 2', font=("Helvetica", 40), size=(40, 1))],
                  [sg.Text('File or Folder Playback'),
                   sg.Combo(sg.user_settings_get_entry('-filenames-', []), default_value=sg.user_settings_get_entry('-last filename-', ''), size=(50, 15),font='_ 20', key='-FILENAME-', bind_return_key=True),
                   sg.FileBrowse('File Browse', size=(10, 1), file_types=(("MIDI-Videos", "*.mid"),)),
                   sg.FolderBrowse('Folder Browse', size=(12, 1), target='-FILENAME-', font='Helvetica 14')],
                  [sg.Col([[sg.Button('Clear History')]], element_justification='r', expand_x=True)],
                  [sg.Text('_' * 250, auto_size_text=False, size=(100, 1))],
                  [sg.Checkbox('Loop Song or Playlist', size=(20, 1), key='-LOOP-'),
                   sg.Text('Choose MIDI Output Device', size=(22, 1)),
                   sg.Listbox(values=self.PortList, default_values=[default_port, ], size=(30, len(self.PortList) + 1), key='-LISTBOX-')],
                  [sg.Text('_' * 250, auto_size_text=False, size=(100, 1))],
                  [sg.Button('PLAY!', size=(10, 2), bind_return_key=True, button_color=('red', 'white'), font=("Helvetica", 15)), sg.Text(' ' * 2, size=(4, 1)), sg.Cancel(size=(8, 2), font=("Helvetica", 15))]]
        window = sg.Window('MIDI File Player 2022', layout, auto_size_text=False, icon=icon,
                           default_element_size=(30, 1), button_color=('white', 'black'),
                           font=("Helvetica", 15))

        while True:
            event, values = window.read()
            if event == 'PLAY!':
                sg.user_settings_set_entry('-filenames-', list(set(sg.user_settings_get_entry('-filenames-', []) + [values['-FILENAME-'], ])))
                sg.user_settings_set_entry('-last filename-', values['-FILENAME-'])
                window['-FILENAME-'].update(values=list(set(sg.user_settings_get_entry('-filenames-', []))))
                break
            elif event.startswith('Clear'):
                sg.user_settings_set_entry('-filenames-', [])
                sg.user_settings_set_entry('-last filename-', '')
                window['-FILENAME-'].update(values=[], value='')
            elif event == sg.WIN_CLOSED or event == 'Cancel':
                break
        window.close()
        # return values if button == 'PLAY!' else (None for x in range(8))
        return event, values


    #--------------------------------------------- DEFINION OF PLAYER GUI ----------------------------
    # ---------------------------------------------------------------------- #
    #  PlayerPlaybackGUIStart                                                #
    #   Startup the main player GUI that will be 'refreshed'                 #
    # ---------------------------------------------------------------------- #
    def PlayerPlaybackGUIStart(self, NumFiles=1):
        # -------  Make a new Window  ------- #

        window = sg.Window('MIDI File Looper & Player 2022', auto_size_text=True, default_element_size=(30, 1),  icon=icon, font=("Helvetica", 25))


        layout =[[sg.T('MIDI File Looper & Player', size=(30, 1), font=("Helvetica", 25))]]
        self.TextElem = sg.T('Song loading....', size=(40, 2), font=("Helvetica", 14))
        self.SliderElem = sg.Slider(range=(1, 100), orientation='h', size=(20, 10), key='-SLIDER-', enable_events=True)
        self.ListBox = sg.Listbox(values=[], size=(30, 10), key='-LISTBOX-', font='Helvetica 12', enable_events=True)
        layout += [[self.TextElem], [self.ListBox],[self.SliderElem]]

        layout += [
                    [sg.Button('⏸', key='PAUSE', button_color=(sg.theme_text_color(), sg.theme_background_color()),
                               border_width=0,
                               font=("Helvetica", 15), size=(10, 2)), sg.T(' ' * 3),
                     sg.Button('⏭', key='NEXT',
                               border_width=0, button_color=(sg.theme_text_color(), sg.theme_background_color()),
                               size=(10, 2), font=("Helvetica", 15)), sg.T(' ' * 3),
                     sg.Button('⏮', key='Restart Song',
                               border_width=0, button_color=(sg.theme_text_color(), sg.theme_background_color()),
                               size=(10, 2), font=("Helvetica", 15)), sg.T(' ' * 3),
                     sg.Button('⏪', key='Rewind',
                               border_width=0, button_color=(sg.theme_text_color(), sg.theme_background_color()),
                               size=(10, 2), font=("Helvetica", 15)),
                     sg.T(' ' * 2), sg.Button('⏏', key='-EXIT-',
                                              border_width=0, button_color=(sg.theme_text_color(), sg.theme_background_color()),
                                              size=(10, 2), font=("Helvetica", 15))],
                    [sg.CB('Enable Pedal Hack', True, key='-PEDAL HACK-', font='_ 10')],
                    [sg.CB('Enable Velocity Hack', key='-VELOCITY HACK-', font='_ 10'), sg.T('Threshold', font='_ 10'), sg.Input('0', s=6, k='-VELOCITY THRESHOLD-', font='_ 10')],
        ]
        layout += [
                    [sg.T('Tempo', font=("Helvetica", 15), size=(6, 1)),
                     sg.Slider(range=(-7, 7), default_value=0, size=(10, 20), orientation='h', font=("Helvetica", 15), key='tempo'),
                     sg.T(' ' * 10),
                     sg.T('Volume', font=("Helvetica", 15), size=(7, 1)),
                     sg.Slider(range=(-6, 6), default_value=0, size=(10, 20), orientation='h', font=("Helvetica", 15), key='volume')],
                    [sg.Checkbox('Loop Region', size=(10, 2), key='loop')],

                    [sg.Button('', key='Set Loop A', image_data=button_loop, image_size=(50, 50), image_subsample=2, border_width=0, button_color=(sg.theme_text_color(), sg.theme_background_color()), size=(10, 2), font=("Helvetica", 15), pad=((90, 175), 3)),
                     sg.Button('', key='Set Loop B', image_data=button_loop, image_size=(50, 50), image_subsample=2, border_width=0, size=(10, 2), button_color=(sg.theme_text_color(), sg.theme_background_color()), font=("Helvetica", 15))],]

        self.slidera_elem = sg.Slider(range=(-20, 20), default_value=0, size=(20, 20), font=("Helvetica", 15), orientation='h', key='loopa')
        self.sliderb_elem = sg.Slider(range=(-20, 20), default_value=0, size=(20, 20), font=("Helvetica", 15), orientation='h', key='loopb')

        layout += [[self.slidera_elem, self.sliderb_elem,
                    sg.Button('', key='Clear Loop',
                              image_data=button_stop, image_size=(50, 50), image_subsample=2,
                              border_width=0, button_color=(sg.theme_text_color(), sg.theme_background_color()),
                              size=(10, 2), font=("Helvetica", 15))]]

        self.LoopAText = sg.T("----", size=(5, 1), pad=((90, 130), 3))
        self.LoopBText = sg.T("----", size=(5, 1))

        layout += [[self.LoopAText, self.LoopBText]]

        window.layout(layout).finalize()
        self.window = window

    #------- Refresh the playback GUI interface.... important to call on a regular basis!!   ------- #
    # ---------------------------------------------------------------------- #
    #  PlayerPlaybackGUIUpdate                                               #
    #   Refresh the GUI for the main playback interface                      #
    # ---------------------------------------------------------------------- #
    def PlayerPlaybackGUIUpdate(self, DisplayString):
        window = self.window
        if 'window' not in locals() or window is None:          # if the window has been destoyed don't mess with it
            return PLAYER_COMMAND_EXIT
        self.TextElem.Update(DisplayString)
        button, values = window.read(timeout=0)
        self.values = values
        self.event = button
        if values:
            self.Tempo = int(values['tempo'])
            self.Volume = values['volume']
            self.LoopRegion = values['loop']
            self.AMarkerAdjustment = int(values['loopa'])
            self.BMarkerAdjustment = int(values['loopb'])
            self.pedal_hack = values['-PEDAL HACK-']
            self.velocity_hack = values['-VELOCITY HACK-']
            self.velocity_threshold = int(values['-VELOCITY THRESHOLD-'])
        else:
            return PLAYER_COMMAND_EXIT
        # print('Back from read', button)
        if button == 'PAUSE':
            return PLAYER_COMMAND_PAUSE
        elif button == '-EXIT-':
            # output_element.TKOut.Close()
            del (window)
            print(button, 'pressed')
            return PLAYER_COMMAND_EXIT
        elif button == 'NEXT':
            return PLAYER_COMMAND_NEXT
        elif button == 'Set Loop A':
            return PLAYER_COMMAND_SET_A
        elif button == 'Set Loop B':
            return PLAYER_COMMAND_SET_B
        elif button == 'Clear Loop':
            return PLAYER_COMMAND_CLEAR_LOOP
        elif button == 'Restart Song':
            return PLAYER_COMMAND_RESTART_SONG
        elif button == 'Rewind':
            return PLAYER_COMMAND_REWIND
        elif button == '-SLIDER-':
            return PLAYER_COMMAND_SLIDER
        elif button is None:
            return PLAYER_COMMAND_EXIT
        return PLAYER_COMMAND_NONE



def GetCurrentTime():
    '''
    Get the current system time in milliseconds
    :return: milliseconds
    '''
    return int(round(time.time() * 1000))



# ---------------------------------------------------------------------- #
# MAIN - our main program... this is it                                  #
#   Runs the GUI to get the file / path to play                          #
#   Decodes the MIDI-Video into a MID file                               #
#   Plays the decoded MIDI file                                          #
# ---------------------------------------------------------------------- #
def main():
    log.info('In main {}'.format(GetCurrentTime()))
    sg.SetOptions(border_width=1, element_padding=(4, 6), font=("Helvetica", 10), progress_meter_border_depth=1, slider_border_width=1)
    pback = PlayerGUI()

    button, values = pback.PlayerChooseSongGUI()
    midi_port = values['-LISTBOX-']
    file_or_folder = values['-FILENAME-']
    if button != 'PLAY!':
        sg.PopupCancel('Cancelled...\nAutoclose in 2...', auto_close=True, auto_close_duration=2)
        exit(69)
    if midi_port: midi_port = midi_port[0]
    # ------ Build list of files to play --------------------------------------------------------- #

    # Priorities for downloading are:
    #   YouTube Playlist
    #   YouTube link
    #   Batch Folder
    #   Individual Download
    filelist = []

    if os.path.isdir(file_or_folder):
        filelist = os.listdir(file_or_folder)
        filelist = [file_or_folder+'/'+f for f in filelist if f.endswith(('.mid', '.MID'))]
        filetitles = [os.path.basename(f) for f in filelist]
    elif os.path.isfile(file_or_folder):       # an individual filename
        filelist = [file_or_folder,]
        filetitles = [os.path.basename(file_or_folder),]
    else:
        sg.popup_error('*** Error in Player... nothing to play found in mv_file ***')
        exit(666)
    filelist.sort()
    # ------ LOOP THROUGH MULTIPLE FILES --------------------------------------------------------- #
    playback_window = pback.PlayerPlaybackGUIStart(NumFiles=len(filelist) if len(filelist) <=10 else 10)
    port = None
    cancelled=False
    loop_point_a = 0
    loop_point_b = 0
    # print(f'filelist = {filelist}')
    song_names = []
    song_dict = {}
    for file in filelist:
        song = os.path.basename(file)
        song_names.append(song)
        song_dict[song] = file
    pback.ListBox.update(values=song_names)
    while True:
        # Loop through the files in the filelist
        print('**** STARTING to loop through files! ****')
        now_playing_number = 0
        while True:
            # now_playing_number = 0 if now_playing_number >= len(filelist) else now_playing_number+1
            # for now_playing_number, movie_filename in enumerate(filelist):
            movie_filename = filelist[now_playing_number]
            print(f'Starting a new song with number {now_playing_number}')
            display_string = 'Playing Local File...\n{} of {}\n{}'.format(now_playing_number+1, len(filelist), movie_filename)
            pback.ListBox.update(set_to_index=now_playing_number)
            movie_title = filetitles[now_playing_number]
            # --------------------------------- REFRESH THE GUI ----------------------------------------- #
            pback.PlayerPlaybackGUIUpdate(display_string)

            if pback.event == '-LISTBOX-':  # if a new track was chosen
                chosen = pback.values['-LISTBOX-']
                print(f'Choosing new song = {chosen}')

            # ---===--- Output Filename is .MID --- #
            midi_filename = movie_filename

            # --------------------------------- MIDI - STARTS HERE ----------------------------------------- #
            if not port:            # if the midi output port not opened yet, then open it
                port = mido.open_output(midi_port if midi_port else None)

            try:
                mid = MidiFile(filename=midi_filename)
            except:
                print('****** Exception trying to play MidiFile filename = {}***************'.format(midi_filename))
                sg.Popup('Exception trying to play MIDI file:', midi_filename, 'Skipping file')
                continue

            # Build list of data contained in MIDI File using only track 0
            pback.Name = ''
            midi_track_info = []
            for msg in mid.tracks[0]:
                    # Track Name Meta Messsages
                try:
                    if msg.name:
                        pback.Name = msg.name if not pback.Name else pback.Name
                        midi_track_info.append(msg.name)
                except:
                    pass
                # print(msg)
            # print(midi_track_info)
            midi_length_in_seconds = mid.length
            display_file_list = '>> ' + '\n'.join([f for i, f in enumerate(filelist[now_playing_number:]) if i < 10])
            next_song = paused = False
            midi_start_point = 0
            prev_pedal = 0
            pedal_going_up = False
            prev_velocity = 0
            ######################### Loop through MIDI Messages ###########################
            while(True):
                start_playback_time = GetCurrentTime()
                starting_midi_message_number = loop_point_a+pback.AMarkerAdjustment if pback.LoopRegion else midi_start_point
                print(f'Starting playback at {starting_midi_message_number}')
                port.reset()
                total_midi_messages_in_track = max([len(t) for t in mid.tracks])
                for midi_msg_number, msg in enumerate(mid.play(starting_message_number=starting_midi_message_number)):
                    midi_msg_number_total = midi_msg_number + starting_midi_message_number
                    #################### GUI - read values ##################
                    if not midi_msg_number % 4:              # update the GUI every 4 MIDI messages
                        t = (GetCurrentTime() - start_playback_time)//1000
                        display_midi_len = '{:02d}:{:02d}'.format(*divmod(int(midi_length_in_seconds),60))
                        display_midi_msg_num = f'{midi_msg_number_total} of {total_midi_messages_in_track}'
                        display_string = '{}\nNow Playing {} of {}\n{}\n              {:02d}:{:02d} of {}\n{}\nPlaylist:'.\
                            format(display_midi_msg_num, now_playing_number+1, len(filelist), movie_title, *divmod(t, 60), display_midi_len , pback.Name)
                         # display list of next 10 files to be played.
                        # pback.SliderElem.Update(t, range=(1, midi_length_in_seconds))
                        rc = pback.PlayerPlaybackGUIUpdate(display_string + '\n' + display_file_list)
                        if rc == PLAYER_COMMAND_EXIT:
                            cancelled = True
                            break
                        pback.SliderElem.Update(midi_msg_number_total, range=(1,total_midi_messages_in_track))
                        if pback.event == '-LISTBOX-':  # if a new track was chosen
                            chosen = pback.values['-LISTBOX-'][0]
                            song_index = song_names.index(chosen)
                            print(f'Choosing new song = {chosen} index = {song_index}')
                            next_song = True
                            now_playing_number = song_index
                            break

                    else:       # fake rest of code as if GUI did nothing
                        rc = PLAYER_COMMAND_NONE
                    mid.tempo_scaler = pback.TempoTable[int(pback.Tempo + len(pback.TempoTable)/2)]
                    if paused:
                        rc = PLAYER_COMMAND_NONE
                        while rc == PLAYER_COMMAND_NONE:        # TIGHT-ASS loop waiting on a GUI command
                            rc = pback.PlayerPlaybackGUIUpdate(display_string)
                            if rc == PLAYER_COMMAND_SET_A:
                                loop_point_a = midi_msg_number_total+1
                            elif rc == PLAYER_COMMAND_SET_B:
                                loop_point_b = midi_msg_number_total-1
                            time.sleep(.25)

                    # if pback.LoopRegion and midi_msg_number < starting_midi_message_number:
                    #     continue
                    if pback.LoopRegion and loop_point_b != 0 and midi_msg_number_total >= loop_point_b+pback.BMarkerAdjustment:
                        print(f'Loop point B reached.  Message num = {midi_msg_number_total}')
                        break


                    #################### MIDI Message Manipulation ##################
                    if pback.pedal_hack:
                        if msg.type == 'control_change' and msg.control == 64:
                            # print(f'pedal = {msg.value}')
                            # cur_pedal = msg.value
                            if msg.value < 64:
                                msg.value = 0
                            # if cur_pedal > prev_pedal and not pedal_going_up:
                            #     msg.value = 0
                            #     pedal_going_up = True
                            # if cur_pedal == 127:
                            #     pedal_going_up = False
                            # print(f'NEW pedal = {msg.value}')
                            # prev_pedal = cur_pedal
                            # if msg.value <= 2:
                            #     msg.value = 0
                            #     print('** TURNING OFF **')
                            # print(sg.obj_to_string_single_obj(msg))

                    # -------  VOLUME modification  ------- #
                    if int(pback.Volume):
                        if msg.type == 'note_on':
                            velocity = int(pback.VolumeAdjustmentTable[int(pback.Volume)+6] * msg.velocity)
                            msg.velocity = velocity if velocity < 127 >= 0 else 127
                    #------- Remap all channels to ZERO if requested in GUI  ------- #
                    if pback.RemapChannels:
                        try:
                            msg.channel = 10 * (msg.channel == 10)
                        except:
                            pass

                    ############# VELOCITY HAC########################
                    if pback.velocity_hack and msg.type == 'note_on':
                        sg.Print(msg.velocity)
                        if prev_velocity != 0 and msg.velocity > prev_velocity + pback.velocity_threshold:
                            sg.Print(f'Velocity corrected. # {midi_msg_number} {midi_msg_number_total} note: {msg.note}  vel: {msg.velocity}  prev: {prev_velocity}')
                            sg.Print(sg.ObjToStringSingleObj(msg))
                            msg.velocity = prev_velocity
                        prev_velocity = msg.velocity
                    ####################################### MIDI send data ##################################
                    if not (pback.PlayOnlyChannel0 and msg.channel != 0):
                        port.send(msg)

                    # -------  Execute GUI Commands  after sending MIDI data ------- #
                    if rc == PLAYER_COMMAND_EXIT:
                        cancelled = True
                        break
                    elif rc == PLAYER_COMMAND_PAUSE:
                        paused = not paused
                        port.reset()
                    elif rc == PLAYER_COMMAND_NEXT:
                        print('NEXT SONG')
                        next_song = True
                        # now_playing_number += 1
                        break
                    elif rc == PLAYER_COMMAND_REWIND:
                        midi_start_point = midi_msg_number_total - 40
                        break
                    elif rc == PLAYER_COMMAND_SET_A:
                        loop_point_a = midi_msg_number_total +2
                        # pback.LoopAText.Update(loop_point_a)
                        print(f'Setting Point A = {loop_point_a}')
                    elif rc == PLAYER_COMMAND_SET_B:
                        loop_point_b = midi_msg_number_total+2
                        # pback.LoopBText.Update(loop_point_b)
                        print(f'Setting Point B = {loop_point_b}')
                    elif rc == PLAYER_COMMAND_CLEAR_LOOP:
                        loop_point_a = 0
                        loop_point_b = 0
                        pback.slidera_elem.Update(0)
                        pback.sliderb_elem.Update(0)
                        # pback.LoopAText.Update("----")
                        # pback.LoopBText.Update("----")
                    elif rc == PLAYER_COMMAND_RESTART_SONG:
                        loop_point_a = loop_point_b = midi_start_point = 0
                        # pback.LoopAText.Update("----")
                        # pback.LoopBText.Update("----")
                        break
                    elif rc == PLAYER_COMMAND_SLIDER:
                        midi_start_point = int(pback.values['-SLIDER-'])
                        break
                    pback.LoopAText.Update(loop_point_a+pback.AMarkerAdjustment if loop_point_a else '----')
                    pback.LoopBText.Update(loop_point_b+pback.BMarkerAdjustment if loop_point_b else '----')
                else:
                    next_song = True
            #------- DONE playing the song   ------- #
                if next_song:
                    next_song = False
                    break
                if cancelled:
                    break

            port.reset()                    # reset the midi port when done with the song
            print('after reset')
            if cancelled:
                break
            now_playing_number = (now_playing_number + 1) % len(filelist)                   # Increment to MAX then roll over to 0
            # now_playing_number += 1
        print(f'Cancelled = {cancelled}')
        if cancelled:
            break
    # sg.sprint('The delta times for midi playback are', *mid.delta_times)
    exit(69)

# ---------------------------------------------------------------------- #
#  LAUNCH POINT -- program starts and ends here                          #
# ---------------------------------------------------------------------- #
if __name__ == '__main__':
    # TODO - in the future, simply add a check for command line parm to autoplay using command line
    icon = b'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'

    button_exit = b'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'

    button_loop = b'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'

    button_next = b'iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAACxIAAAsSAdLdfvwAAB8WSURBVHhezZ17sJZVvccfN8ZFASER2GyQ5KLizgtC4x3MQjPUtJS0qaYxm2aOnVNNnZrKM+lMTae/Ujs459SMWmraTsyOIaOmJ0jykopIXFS2RggbNijiVm6Fnt9n8X5ff/vHet797s3e4HfmO2s961nPb631/T3r8lze5z2oeA+jqalpUENDw5jx48c3jhw5ctKQIUOOPeaYY462XaOMQxwHG8Gbxg7Hjc8///wLHR0dq9rb21evWbOm7e23316/bt267bbvPYn3jEMOOuig4n3ve1//iRMnjm5ubp5hzjjniCOOONUc0mi7hxobUkbDO++8U4nVBjYd3ja+YQ5p27Rp0+PmlEeWL1++qLW1dcM//vGPXfXa7GsccIeMGDGi36RJk44/7rjj5pgzZltSs7Ef+6JIPRUtOMZv7zYuN6fMX7FiRcvq1auXbd68mbQDhgPikIMPPvggc8IYc8InrDd8bsCAASdY8iHs86LXE68F74g64tt27tz5nPWa28w5vzPnrP/nP//ZszNgH7DfHTJlypTJM2fOvNqGpM/b5nDScmLXG5ZBQtcbAhffYkPaLxcuXDh35cqVL1bS9gverU0fwnpEg/WIKTNmzPi6OeJSa/hhpOdEFuN2TFM8By92jJeladuHZn+rOebuRYsW/cR6zErrMcxDfYo9JfchzBHDPvrRj17b2Nh4pW2yIioVF9qkW43XSoM6zsOLGmkLhJpp/jjFK+hoa2u7+Q9/+MO15pjXK2l9gj5zyPvf//7+1iPmnHjiiT+who0nLQrpiehirW1/DMxBooqILuEVL9v29LaAlbdm6dKl11iPaXnttdd2pcReRq87hMofddRRE+bMmXODTdbnW1I/CeeFhF50cffu3dm4qONkIweJmBMd9uvXLxv3lA1Rdg27bfJf0NLS8tWXX375pbI69BS96hBrSMMFF1zwqZNOOum/bHMkaV44L6iI6LWoPIg0cODAYtCgQcVhhx2WQrtuKfr3759CYNcTxa5du1K4ffv2YuvWrSncsWNHsiPxCWuRPCJOIATeOYb2Z5999iu///3v55ntXptbes0hdj0x+OKL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'

    button_pause = b'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'

    button_restart = b'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'

    button_rewind = b'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'

    button_stop = b'iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAAACXBIWXMAAAsSAAALEgHS3X78AAAd9UlEQVR4nM19aWwc153nr6qrL3Y32c2rm4d4ti7SpijRQnRg5cSRrFhy7ASTKDEw9ofB5lNmdjAf9tsAyQABZr/NzM5ksftldpHMxgZhO/FuJAO216swK0eKRB0USVFSkxTFq3n0waOv6qP2g/kqr1+/V1WkKMl/4KG6q6ve8fu9//GOqpbwFZaWlha3LMvN7e3tTY2NjWGfz3dg//79+wAEAfio5N26ZRPABpWW7t+//2BjY2NieXk5MjMzs1gqlRbm5+czz6M9VkR63hUgIkkS7Ha7o7u7O9Tb23uqpaXllYaGhmOyLDcBqAYgk2s1TbOcJyUlAOulUmlxZWXl6vz8/OdjY2NDk5OT0Xw+r1rN82nLcyekvr7eFg6HX+zp6bnQ3d19HkAvABtQCfxOQWOIob8XAYxNTk5eHB8fH4xEIndXV1eLOypkl+S5EKIoihQOh5t7enre7O3tfdvpdPYBqALKQbfy2UhoIix8TudyuZGxsbFfjo+PfxSJRBYKhcIzV5tnTsjBgwf3vvzyyz9uaWl5B0AA4INt9SgSArTVI/M5MT8//4vf/e53P793797D7bdy5/JMCFEURQ6HwwdPnTr1Ny0tLd+TJKkG4INMEvudPUffxwoNNvtZdI69byv/tfn5+feHhob+IRKJ3CsUCqXdxIVb96ddQDgc9p8+ffqnTU1Nf4EvIyIhuJqmoVQqVRDBOyciRUSAJEmQZdnwHH0fnReAjcXFxX/97LPPfhqJRJJPE6+nRkhtba3j1KlTFw4dOvQzSZLaAT4BNOgkGX3nkVLRKA7oBHjyWfRdpEVbdZ65c+fO3w4NDQ3G43H1aeC264RIkoTOzs6uCxcu/JPT6XwNgM0KCSQVi0XuZ5YcK4TwQJdlGTabjfvZCjkAirlc7uPBwcG/np6entrtcHlXCZFlWX799df/rL+//18ANALlWsHr/cVi0TCRa2RZhsvlgtvtRk1NDdxuN+x2OxwOB+x2OwAgn89DVVXk83lkMhmsra0hk8kgm82iVCrp4NtsNsPE0yKgXFsALN++ffsvf/vb335QKpV2zbfsGiH19fXe73znOz9pbm7+K03TnCLfwJJQKBS4R0mSUFNTg+bmZrS2tqK2thYulwsul6vC7rNCl5nNZpHNZhGPxzE3N4eFhQWsra1B0zTYbDYoisI90uQY+JrcwsLCP//mN7/5u9XV1c3dwHFXCDly5Ejr+fPn3wNwkvUThAi6txcKBW4CgFAohL1796K9vR0+n49rSsgRqBz08cpmzd7GxgZmZmbw8OFDRKNRAICiKNxEaxWv7K3PVy5evPjDmzdvzj0plk9MyEsvvdR75syZd20224u8SIjWCBr8fD6vHz0eD3p6ehAOhxEIBMp6Kc++0+QAZWEqVyN5forUJ5FIIBKJYHx8HKlUCna7HYqi6EeaGFpj2FQsFu9++umnb924cWPsuRFy+PDhgddee+3XAPbwACFawRJB7LzP50N/fz/279+PqqqqCnNBTAgNCi8sZQeWog7B+iWamHQ6jfv37+P27dvY2Ngo8090HehAgHX6AGY//vjj7966dWt4p5jumJCBgYEzZ86c+TdZlhtFIBB/kM/n9aSqKlwuF44ePYoDBw7A7XaXAa4oChwOhw6GkXlixYgYWlvoDsJqbyaTwcTEBK5fv45sNqvXgyTaz/C0pVQqLX/66ad/Pjw8/OlOcLXt5Kb+/v6BV1999QMeGWwDVVVFLpdDLpeDqqrYt28fzp49i46ODrjdbh18l8sFr9cLr9erR1Aik0U0hXW6rI8R+R+eGSLJbrejsbER3d3dyGQyWFpa0s0frwNwJi49nZ2dZ1Op1P+NRqOL28V22xpy5MiR3ldfffVjAHtYB0qTQWuEqqrwer04ffo09uzZo/c2RVHgdDrhdrvhdDq5DtNo7okVMw0RjYHoOtOmNZ/PY3Z2Fp999hk2NzfLNJfUn/UtVB1nP/nkk9du3ry5LZ+yLQ3p7+9vPXPmzK8lSdrLaxxrnohmdHR04Ny5cwiFQnA6nXA4HHA6nfD5fPB6vXA4HIaO26znG11vNNhjr2MjKVmW4fP50NXVhWQyidXV1QqtEHUQSZJqOjs7/10qlfrf0Wh0fdcJqaur8164cOE3kiS9ZEaGqqr6YOzYsWP4xje+Aa/Xq5Ph9XpRU1MDl8tlGkkZjaKtkse7nje3xY7cyTmHw4FwOAxZljE3N6eH6BZICYbD4a9NTEwMZjIZS1MtlgiRZVn+/ve//zOPx/NDdtRNzBRNRi6XAwCcPn0afX19cDqdcDqdcLlcqK6uhsfj0SMWoykMHqBmk4K8ns8LU0XnRflIkoRgMIiamhpMTU0JSaGPW1i1tbS0OO7evft/NAvzLKaESJKEs2fPfq+7u/s/aZqmmJGRzWahKArOnTuHffv26WRUVVXB7/frI20RCWY9XkQOT3t4ZBkBzyNWlsunTWpra9HQ0ICpqSmoqmro58jR6/UOeL3eicnJyfEnJqS9vb3rlVde+RBAjZGZIv5CURS88cYb6Ojo0Mnw+Xyorq4u0wqrZPBANurdVrTLLNGdkXdvTU0Nmpqa8PDhQ6iqyiWBESUYDL48Nzf34draWmLHhPj9fscPfvCD/26z2Q7TpoqO5WkzpWkazp8/j46OjjLHXV1dbWnkLSJDRMx2zM12Ek0IORJNIeL1elFXV4f79+/rc2+ie7ew8+zdu7f7/v37H2SzWeG6vSEhX//6198KhUL/EYAsmgohZJRKJZw9e7bMTPl8Pvh8vgoijKa8RYRYJYMW1pzw7qWvY7+zv7FlVFdXo6amBpFIBKVSiVtGGdg2W7fT6XwYiURGtk1IR0eH/9SpU4OSJAVEZBBTpaoqTpw4gUOHDlWYqe1EUWZmR2AOuCTwTA/PrDzJtQDg9/shSRIePXpUUV/2HkmS5IaGhoHFxcX/kUwms5YJURRFPnfu3N97PJ6zvFE4baZyuRy6urrwzW9+U0gGDbJV+y9qFAuambYYfTcDnz0nIiUUCmF5eRmrq6tW8vXX1dW5x8fHPymVShVRF5eQzs7OniNHjvwcgJM3qqUJ8fl8eP311/VxBommRGEsz8ZvlwgrpPCuYYG2og0irZQk3TdA0zSEQiFEIhFkMpmKNtH3AIDH4+ldWlr6KJFIrFgi5Fvf+tbfe73eY7x5KuI3VFVFoVDAt7/9bTQ1NenjjNra2rJoygh8nnrziBABaCRGBLFlAShz2ryyRfkTUhRFQW1tLcbGxridjinbWVNT4xwdHf1fbL4VhHR3d+89fPjwP2qa5gLAne8h2nHw4EEcPXpUH4HT4wzWBD1J2GmFADMx0hT6d/qcVSGkeL1eJJNJLC0tGQYQmqbB4/F0r66ufpBIJOJ0XmWxnM1mk44ePfpjbI05RIs6+XweLpcLJ0+e1CfZPB4P3G63JTJYE8UDYTdIEIkRKaKAg7fmTqbi6UWtkydPwuVy6ROV9BoMvVEDQM3Ro0d/bLPZyhpaRkhbW1tzY2PjO6IpdXri8Pjx4/D7/bDb7boj34428AAhn58mGWw5IrNmFP2JSLHb7fD7/Th+/HgZVgQ/FtfGxsZ32tramul6KfSXcDj8JoAAfROrIfl8HtXV1ejt7dV7htfrhd1uFzptUcOvXbuGWCyml88uv7L7r9gjD2T2aFQn+kgkEAjg8OHDFeSwdbTZbGVHgo/dbkdvby+uX7+OVCoFRVH0XTNkrELVNxAOh9+cnp7+LxWEBAIBW1dX19tG6+FEDQcGBvSVPhJZmYHPOx+Px7GwsLCt7UC8vVpGm+hY8lhtZCOh7u5uHD58uIIIkpcsy3r+5LMsyzrwiqLA7XZjYGAAn3/+OfL5fMXqIp1vV1fX24FA4L8lEokiQJmsPXv2vGi32/uMFnAKhQK8Xi96e3v1VTev11u21m02zmB7sdlGBKPELsPyfjc7R/KgVwVZn8IzYzzTRe8B6O3thdfrLasjr/PY7fa+PXv2vEh4kEnBnZ2dFwBUGZmrQqGAvr4+fUOCw+HQtWO70RM5iojglS0igt7Txa6Xi86JSKQ1WgdJ4EvYRG+GqKqqQl9fH9exM1pc1dnZeYGUJwOAoiiO1tbW8yLtII0AgAMHDuhLlx6Px5KJYkmgTYCZhphpDW+jnRXgRYk2cSIN50WMbCSmKAoOHDgAAIbRlqZpaG1tPa8oikMnpLW1NaRpWi99EW8/VUtLC2pra2Gz2WC32+F2u03NkihqkiSJSz57tGKueATwNEREElsmT6N5gQFvwEuTUltbi5aWlgqNZnHWNK23tbU1pBPS1dV1CtRjZCKT1dPTo2uHy+WCoiiGGsIzUayIHDTPbFklZzsawpLB0xCetoi0htWSnp4eM5MFALYtDr6Msurr618plUpcgEhmW35GL8zlclnyFSLtoAlhybfq3Nnr6ZCZCL0pgQWXRElEW0loSmswT0uMzBarJZ2dnZAkSa+zzWYrC39JHerr618B8G9KQ0OD2+/3HxNpB2l0IBBATU1N2V5XkTyJDxGRY0QKzy6T/Hmdg4SdhAx2nMHrOORaHhkEYJYgm82GmpoaBAIBJJPJsnrS4bMkSfD7/ccaGhrciizLzQCaWDJYP9LW1lbWC9LpNACURVki4I2EBdLIubP+gachHHNQETGxWkETSDSEJyJrYKYxbW1tiMViZf6DkEjVs0mW5WY5GAw2AahmG8MC09HRUTGdkM/nkU6ny8JFoyNPjCKtnUZYvLEGL1Dg+SzeLIAVX2JESEdHh1CTqc5THQwGmxS/3x/WNE1mL6BBkmUZ9fX13PkdAPpCP9nwJiKBd86oXCNnzwOWpx1sx6AjI9pfkCPvXqP8rJBCsDPRZNnv94cVt9t9wAwQt9utz+SyhJCkaRoKhQIZffKUgSu88oxMl5kfoe0yDSBdT3rKA/iTGRNpCCtWoy+SCH6qqnL9CBG3231AaWtr20eDQ38mlfR4PIZRFdvzaSdnJrwes5PIi3XoPPB4YyTWZxj5EHIf7eDZcnjJ5XLB4/Egm81W1JHuPG1tbfsUTdOCLAEsQPSSrFFFWGF7qpEYlS8aFxH/wGoIqRevfjQ5bLRjpB3kPl6beBjQmmKz2eD3+/W9wXR7GC0JKth6dpwHDkler9eSZhiRIyKGF6YaaYtIU3jmigYFQBkAdJQjis7ouos0zwgDOnm9XtNyAPgUTdP0h/lFiax1GAFrVRNoicfjSCQScLvdXDJ4WmOVEJoMAj6tDbyySL7bFTNMJEmC3W43xHhLfFwNYSvrdDorCiBHq76CJ6urq7h79y40TdMfeXY6nWUdgFcf1nwRs0UDQQ/+2DzItfS8FZmt3QkhpEyeaSRHp9NpxTT6FE3TvHTFeT3I4XDsqJJWGkGiM/L8Bf1YNLvmQDtiI6dOk0m3hY2A6OlynlnaTXE4HFxs6ToC8JYt4bK96WmLkV8h69GiR6jZgSBQ/mgz+8Aoncizi89LRFEW8OXk4qbGedCfFjLw220xM3dGoSRragBwx0dmgQhb3tMSFkOehkiStKlomrYBoI7+gRXyAI5RNLQToUf120nEOZOlY2L32SmL7eZL6rITYbFgjwRD3n1USL2hANgQAUoqSh41oAvgZbxd2Q5oNNB0w2kHzl63E3J2ImaYaJqGXC5nWMYWMRtEQwx7eyqVMgvXYJYHaysBc81gSWCn/WltofOj1yR2Qo4VwK1gQKdUKmWYx1ZQsaEAWGIBIp/JMZFICKcnjCpGRy68hrLgsMCRgRxtoui6svVh8zF6u48RQTwRREVCDOgQu1gsIpFIcLFlyltSZmdnH7S2thr27s3NTWSzWVRVVZlqCltxIzNgRAABlCWCJsOMEHb1jg2jRQQZiSj4EeGiaRqy2Sw2NytfFsTmMTc390DJZDIT7IUERFLBVCqFdDoNv98vnELmxdhmNpkHCG2aRGQUi3/aCch2IJKfJEllJBiRwltSMBJeW9lEzyik02n9xTZGyxOZTGZCSSaTEU3TSmBeVEzfUCwWsbq6ilAoZEqIkfNn8zUyTTwySEOIhrDT1/TvIi0x0xQWKFE7jMhgCVldXUWxWNSXJWhTTuVZSiaTEWVlZWURwLqmaX66UeRIKjw1NYWenh7DVS9eMvIjNDg0ESLN4Jkqnsni+RKeprC/iUyWFY0QkVEqlTA1NVVGPIvFFk7rKysri0qpVFrQNG0RgJ9mjW3co0ePrCxDCknhiVWtMCOEdx3PN4he58dOz4jEzESLCCHPH/ICB6rTLpZKpQUlFotlksnkVb/ff1AEgizLiMViSCaTcDgcQkJEU9qsitI+ihBgRoZRZ7BKiBkp5DOPABEhIhxIdJVMJhGLxUx9VDKZvBqLxTIyAMTj8c+NyJBlGcViEZFIxNIWHFFPohsKgAsIm8zmpugXjLEvG+PdKyqH1hS6jjxyzDSCxohgZhY4EA5kAJiZmRnSNK1o5iBHR0fLHkAhO/2MeguvhxEx6rU8MoxIMSPDKik8DTEihG0zjU0+n8fo6KghGVv3FWdmZoaArZ2L0S/fBDkmSVIfMTE8tX/8+DHi8ThcLhdXS0jERNt72oSRyrAawhMS3po5cyOTZeRLjMwXmy+PANGGDJqQeDyOx48fCwehpL4AxrY4+JKQYrGoLi4uXgyFQn1sZehGEcYbGxvLCiZE8NaoaVLoPImGiEJbQoYVs7hdQoxIEfkQM3/BW+sfHR1FsVgs2wNN500kGo1eLBaLKrBlsjRNw9zc3CCANA0YyYSu8PDwMFKpVNlaBG+9m7fsyjaUzdvMNBmZKyOzZWbK6ETXj4ioPWyiMUmlUhgeHi7Lm6MZAJCem5sbJOXpC1SLi4t3VVUdsdvtx0QaYrPZsL6+jpGREZw4cQKFQqHiGTrazNCFk4YQtaVNGAGC1Qx65ZA2D6xtZzWErTd7FI1D6LqSvI2I4O09JoSMjIxgfX1d3zwoCndVVR1ZXFy8S87rhKyvrxdnZ2d/2dXVdYxVfbbyX3zxBfr7+6EoCgqFgt4DiHmi/Qj5TgupYF1dHfbt21dWSdZOGwUIPGEJMSKGN/Zoa2srI4PVeCvakU6n8cUXX3DHOCwxs7Ozv1xfX9ffDlS2hDs7O/tRV1fXz7D1RytsTyMFxONx3LlzB8eOHStTe3ItT0vo3kfAPHHiBE6cOCFS5WcivAjQLKyltYNdSs7n87hz5w7i8bj+Yk+DcDcxOzv7EX2ibJ4gGo0uxGKxX5BK0SDRhCiKgsuXLyMej5etfbMqbGR7zULKpy1mobmRL2TbSb/FNB6P4/Lly2Xv9mWnTEhZsVjsF9FodIGul42tZDabnWxra3sHgIsN/egKZzIZZDIZ7N+/v8IM8HqDqOfztONpawtr9ng+w2iwR5+j39StqiouXbqEx48flwUZgnmstRs3bvxobW0tRtetYiZtfn7+YSwWe589zzp3m82GW7du6e8eZDWFN5I3i8aM0m6QYJas1pd24PT7JqempnDr1q2yEFo0Mo/FYu/Pz89X/L8Vd1SWy+Um29vb3wbgFPVS0oBHjx7hwIEDur0EYElLWO0z0gqr59j6ic7xBn1GAz7RsymkI+ZyOcRiMbz77rvI5XIVL1rmaMjG8PDwv9/Y2LD2eqZ0Oh1rbm5udLvdesRFH+mGbW5uIpFIoLe3lxvV8MSKKTK6xqopY0nhEWFECO9ZFHpahLymSlVVfPjhh5idnS17Rzwd7NALU4lE4r+OjIz8T43Ta7iEaJqmpdPpq+3t7W9JkuTnXUMDE41GoSgKWltbK3yC1Z5sFsbuRERaYkQGz3nzNIOkXC6HoaEhXL16VX8VOT34ZMNdTdNm/vjHP/5wfX2d+/evwic3Nzc3s16vd9Xv97+paVqZr+GFitPT06irq0NDQwN3LLBTAFnZLkFGWmF14Mf6DJqQkZERXLp0CbIsVxDBMd3FR48e/YeJiYk/iupr+FbStbW1ic7OziM2m20fDwwa+GKxiImJCTQ3NyMQCHCv44HEA9DIqW/HwbPRk5XpHSPtoIlQVRX379/H4OAgNE3TNYOsm9PaQTDI5/OXrl69+hNVVXf2mlhVVYvxePxaR0fHW5IkeejfeE64UCjgwYMHaGtrQ3V1NdjrRU7d6Bz9Gy9MNYqYWJ9gNbISjTNoMqanp/Hee+8hn8+X/fELO0im2r38+9///nuJRGLVCHPTN1unUqlEVVXVTCAQeAOAYmYyVFXF+Pg4gsEg/P4/uR86kuKBbAa0GQFW/YKVcJY3zmA147333kM2mzX86wqq0+ampqZ+9ODBgytmeFt6GX80Gp1obm6udrvdJ7YKIAVxP6uqirGxMdTW1qKurq4CcFZEvZ8lYTukGM0QiMySaPRNv2dyZGQEg4ODyOfzVslAIpH4xytXrvxnXlS1I0I0TdNWVlb+sHfv3pclSWozI4X4lHv37kGWZZCNeDxSRJpgBL7ZNVa0wyikZU0UeVn00NAQLl26pPsMK2QAuHL58uUfZbNZ/m7rnRACALlcTs1ms5+EQqEzkiQFaVJEBJVKJTx8+BCLi4tobW3V9yWxc1lG4FvVAitRkxkh7MibHvR98MEHuHbtGmRZ5moGb+yladrd4eHh70ajUUO/sSNCACCRSKyrqjrU1NT0bWy9uZQnbLi7vLyMiYkJBINB+Hw+LojbJYZngraT2Nla2jzR2jE5OYlf/epXmJ2dLVsQYzdGcDRj9tatW9+dnJyc3A7G2/5TsHg8vpLJZIaampq+QyIvnsliUzqdxs2bN5FIJBAMBvWHINkevd0IykqkJPqd5yeIiVpdXcXFixdx6dKlsukQK2ZK07Tl4eHhNyYnJ+9sF98d/UtbIpFYVFX1TigUOisihXymZ4IBYGFhASMjI1AUBYFAAJJUuW7OGyeICNmuVrB/+sWSsbm5iRs3buD999/H48ePK97La6YZmqYt37p1688nJyf/306wfaL57a6uroGXXnrp12D+sY1nw2k7TY61tbU4efIkDh06pP8NEm9bjoVdG7qY1YOtD6lLKpXCnTt3cOXKFcTjce66u4V6zN64ceO7U1NTz/6PJYmEw+He/v7+d2VZfpGNgIzCTHpBq7q6GkePHsULL7yAurq6ssk5I0KMZqKNCKEnCGOxGEZHR3H9+nWsr6+XLcKJtprSE4XkWCqV7t6+ffutSCTy/P56lUh3d3frwMCA/ufERMxAYXuqLMtob29HX18f9u7dC7/fzyWEs9hTViY5ikxbMpnEw4cPMTIygpmZGZRKJcP9vkZr4iS0HR4e/uHk5OTz/3NiItXV1d6vfe1rPwkEAn+laZqTnDeKkFhi6PM2mw11dXXo7OxEd3c3GhoaUFVVBbfbXbGlhhVSTrFYRCaTQTqdxsrKCiYnJzE9Pa2/TEy0T8tIIxkycolE4p+vXbv2d+vr61+dv+8mIsuyfOTIkT/r7Oz8FwCNZuMMngNn1+JpgrxeLzweD+rq6uDxePQ/kCFvmiB/MJPL5ZBKpRCLxbC5uYlUKlWxv5Ymgv5ukQgAWJ6env7LmzdvfjX/4J6WYDDYdfz48X+y2+2vAbA9yehaNABkB5ZljRKE3ry1f/bII4E5FvP5/Md/+MMf/nppaWlqt7F7antuvF6v4+DBgxfa29t/JklSOwseD1izMJe+lj3qDeKAyBLCI4q9ljWHWyHtzMzMzN/eu3dvcHNz86m8TeGpb4IKhUL+F1544aeBQOAvAPh4xJCjkQbxrmHzMJvKMdIAUZCw9X0jkUj86+jo6E+j0WjySTExkmeyK81ms8nBYPDgwYMH/yYQCHxPkqSKaReev6HPGxHBiogY9si7jv6uadpaIpF4/969e/+wtLR0r1gs7pqvEMmz3SYIoLm5eW9PT8+PA4HAO9jaIckDlge8EYm0CHq5IQHMuUQikfjF+Pj4zxcWFiq26jxNeeaEAIAsy1IoFGpuaWl5s6Wl5W1FUfoAVLHXiQA3+w3Y0a6VdKFQGJmfn//l/Pz8R9FodKHE+Vu7py3PhRBafD6fLRgMvtjc3HyhsbHxPIBeUHNsZsBvVxgyigDGlpeXLy4sLAwuLS3d3djYEK53Pwt57oQQkSQJNpvN0djYGGppaTkVCARe8fl8xyRJagJQDc4uy21KCV8+/r24sbFxNZFIfD4/Pz+0vLwcLRaL6m4Tv1P5yhDCk0Ag4JYkqbm+vr7J5/OFXS7Xgaampn0Agvjy1YQkebdu2QSwQaWlxcXFB9lsdmJjYyOyurq6qGnaQiKR4O6J+irI/wdsFxUopGLUlQAAAABJRU5ErkJggg=='

    main()

    exit(69)            # this way I know for sure it exited in my code
