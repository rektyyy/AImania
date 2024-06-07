import ctypes
import subprocess
import time
from threading import Thread

GAME_WINDOW_NAME = "TrackMania Nations Forever (TMInterface 2.1.4.testing)"
GAME_NAME = "TMInterfaceTesting.exe"
GAME_DIR = "C:\Program Files (x86)\Steam\steamapps\common\TrackMania Nations Forever"
class GameLauncher():
    def __init__(self, gameName=GAME_NAME, gameDir=GAME_DIR, windowName=GAME_WINDOW_NAME):
        self.gameName = gameName
        self.gameDir = gameDir
        self.gamePath = gameDir + "\\" + gameName
        self.windowName = windowName
        self.gameThread = Thread(target=self.startGameProcess, daemon=False)
    
    def startGameProcess(self):
        subprocess.run(self.gamePath, cwd=self.gameDir)
        while True:
            time.sleep(0)

    @property
    def isRunning(self):
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, self.windowName)
            if hwnd == 0:
                raise Exception("game not started")
        except:
            return False
        return True
    
    def start_game(self):
        if not self.isRunning:
            self.gameThread.start()

        else:
            print("game already started")

if __name__ == "__main__":
    game_launcher = GameLauncher()
    game_launcher.start_game()   
    

        
    

    