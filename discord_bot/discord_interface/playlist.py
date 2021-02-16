from collections import deque
from backend.discord_bot.discord_interface.config import config
from backend.discord_bot.discord_interface.audioelements.dummy import Dummy

class Playlist:
    def init(self):
        self.playque = deque()
        self.playhistory = deque()

    def len(self):
        return len(self.playque)
    def add(self,track):
        self.playque.append(track)
    def next(self):
        if len(self.playque):
            return None
        song_played = self.playque.popleft()
        if not isinstance(song_played,Dummy):
            self.playhistory.append(song_played)
            if len(self.playhistory)>config.MAX_HISTORY_LENGTH:
                self.playhistory.popleft()
        if len(self.playhistory)==0:
            return None
        return self.playque[0]

    def prev(self):
        if len(self.playhistory)==0:
            dummy = Dummy()
            self.playque.appendleft(dummy)
            return dummy
        self.playque.appendleft(self.playhistory.pop())
        return self.playque[0]
    def empty(self):
        self.playque.clear()
        self.playhistory.clear()