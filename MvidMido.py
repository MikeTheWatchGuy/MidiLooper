import mido
from mido import MetaMessage
from mido.midifiles.tracks import merge_tracks
from mido.midifiles import tick2second
import time


# ---------------------------------------------------------------------- #
#    MidiFile            SUPER-CLASS                                     #
#  This is a super-class of the mido.MidiFile class. It adds one         #
#    attribute to the class to implement tempo and overrides the 'play'  #
#    method                                                              #
# ---------------------------------------------------------------------- #
class MidiFile(mido.MidiFile):
    def __init__(self, **kwargs):
        self.tempo_scaler = 1.0
        self.volume_modification = 1.0
        self.delta_times = []           # used only for DEBUGGING
        self.starting_message_number = 0
        super().__init__(**kwargs)


    def play(self, meta_messages=False, sync_to_system_clock=False, starting_message_number=0):
        """Play back all tracks.

        The generator will sleep between each message by
        default. Messages are yielded with correct timing. The time
        attribute is set to the number of seconds slept since the
        previous message.

        By default you will only get normal MIDI messages. Pass
        meta_messages=True if you also want meta messages.

        You will receive copies of the original messages, so you can
        safely modify them without ruining the tracks.

        """
        sleep = time.sleep
        midi_elapsed_time = 0
        start_of_playback = last_message_time = _GetCurrentTime()
        self.starting_message_number = starting_message_number
        for msg in self:
            # now = _GetCurrentTime()
            # delta_since_last_message = (now - last_message_time) / 1000
            # self.delta_times.append((now - last_message_time, msg.time * 1000))  # used only for debugging
            # sleep_time = msg.time - delta_since_last_message
            sleep_time = msg.time
            # print(f'time = {msg.time} last = {last_message_time} cur = {GetCurrentTime()} delta = {delta}  sleep = {sleep_time}')
            # sleep_time = 0 if sleep_time < 0 else sleep_time

            if self.tempo_scaler != 1.0:   # if tempo is set by user
                sleep_time = msg.time*self.tempo_scaler

            sleep(sleep_time)

            if isinstance(msg, MetaMessage) and not meta_messages:
                continue
            else:
                yield msg                       ########## YIELD'S HERE! ##########

    def __iter__(self):
        # The tracks of type 2 files are not in sync, so they can
        # not be played back like this.
        if self.type == 2:
            raise TypeError("can't merge tracks in type 2 (asynchronous) file")

        tempo = 500000
        for msg in merge_tracks(self.tracks)[self.starting_message_number:]:
            # Convert message time from absolute time
            # in ticks to relative time in seconds.
            if msg.time > 0:
                delta = tick2second(msg.time, self.ticks_per_beat, tempo)
            else:
                delta = 0

            yield msg.copy(time=delta)

            if msg.type == 'set_tempo':
                tempo = msg.tempo

def _GetCurrentTime():
    '''
    Get the current system time in milliseconds
    :return: milliseconds
    '''
    return int(round(time.time() * 1000))
    # return cv.getTickCount()*1000/cv.getTickFrequency()