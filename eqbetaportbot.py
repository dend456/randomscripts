import time, ctypes, win32gui, subprocess, os
from SendKeys import sendKeys
from datetime import datetime

PAUSE = 0.005
OOC_DELAY = 2 * 60
logPath = "C:\\games\\EverQuest\\Logs\\eqlog_Translocator_beta.txt"
mods = ['trakof', 'uzamzene', 'ciltaltike', 'gamon', 'zanif']
spells = [[['commonlands','common','commons','commonland'],['tox','toxx','toxxulia'],['nek','nektulos'],['nro','ro'],['fay','gfay','faydark','greater'],['cazic'],['combine','dread','dreadland','dreadlands','dl'],['nkarana','north']],[['wkarana','west']]]
timeOfLastOOC = datetime(2010, 1, 1)
lastDest = None
lastSpellSet = -1

def findDest(dest):
    for spellset in range(0, len(spells)):
        for spellgroup in range(0, len(spells[spellset])):
            for spell in range(0, len(spells[spellset][spellgroup])):
                if dest == spells[spellset][spellgroup][spell]:
                    return spellset, spellgroup
    return None

def parseLine(line):
    global timeOfLastOOC
    line = line.lower()
    if "tells you," in line:
        line = line.replace("'", "")
        line = line.split(" ")[5:]
        if len(line) < 4:
            return
        if line[3] == "help":
            sendInput("\n/tell {0} commands are \"list\", \"port <destination>\"\n".format(line[0]))
        elif line[3] == "list":
            for spellSet in spells:
                sendInput("\n/tell {} {}\n".format(line[0], ' '.join([s[0] for s in spellSet])))
        elif (line[3] == "port" or line[3] == "load") and len(line) >= 5:
            if line[4] == "list":
                for spellSet in spells:
                    sendInput("\n/tell {} {}\n".format(line[0], ' '.join([s[0] for s in spellSet])))
            else:
                port(line[0], line[4], True if line[3] == "port" else False)
        elif line[3] == "say" and line[0] in mods:
            sendInput("'{}\n".format(' '.join(line[4:])))
        elif line[3] == "tell" and line[0] in mods:
            sendInput("\n/tell {} {}\n".format(line[4], ' '.join(line[5:])))
        elif line[3] == "mimic" and line[0] in mods:
            sendInput("\n{}\n".format(' '.join(line[4:])))
        elif findDest(line[3]):
            port(line[0], line[3], True)
        elif line[3] != "sorry,":
            sendInput("\n/tell {} {}\n".format(line[0], "Unknown command."))
    elif "'hail, translocator'" in line:
        currentTime = datetime.now()
        if (currentTime - timeOfLastOOC).total_seconds() > OOC_DELAY:
            sendInput("8")
            timeOfLastOOC = currentTime

def port(target, dest, cast):
    spell = findDest(dest)
    castPort(target, spell[0], spell[1], cast) if spell else sendInput("\n/tell {} {}\n".format(target, "Unknown destination."))

def castPort(target, spellSet, spell, cast):
    global lastSpellSet, lastDest
    if spellSet != lastSpellSet:
        sendInput("\n/mem port{0}\n".format(spellSet+1), 0.05)
        sendInput("\n/tell {0} loading spells\n".format(target), 12)
    if cast:
        if spell == lastDest:
            time.sleep(2)
        lastDest = spell
        sendInput("\n/target {0}\n".format(target), .5)
        sendInput("\n/cast {0}\n".format(spell+1), 1)
        sendInput("\n/cast {0}\n".format(spell+1), 1)
        sendInput("\n/cast {0}\n".format(spell+1), .05)
        sendInput("\n/tell {0} casting port to {1}\n".format(target, spells[spellSet][spell][0]), 8)
        sendInput("{ESC}", .25)
    lastSpellSet = spellSet
    
def getWindowHandle():
    windows = []
    def enumHandler(hwnd, lParam):
        if win32gui.IsWindowVisible(hwnd):
            if 'EverQuest' in win32gui.GetWindowText(hwnd):
                windows.append(hwnd)
    win32gui.EnumWindows(enumHandler, None)
    return None if len(windows) == 0 else windows[0]

def sendInput(msg, delay=0.0):
    sendKeys(msg, with_spaces=True, with_newlines=True, pause=PAUSE)
    if delay > 0:
        time.sleep(delay)

if __name__ == "__main__":
    hwnd = getWindowHandle()
    if not hwnd:
        proc = subprocess.Popen('c:\\games\\EverQuest\\launchpad.exe')
        time.sleep(10)
        ctypes.windll.user32.SetCursorPos(1200, 700)
        time.sleep(.05)
        ctypes.windll.user32.mouse_event(0x2, 0, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.mouse_event(0x4, 0, 0, 0, 0)
        time.sleep(15)
        sendInput("\n", 20)
        sendInput("\n", 25)
        proc.kill()
        hwnd = getWindowHandle()
    s = os.stat(logPath, follow_symlinks=True)
    logSize = s.st_size
    port('none', 'combine', False)
    while True:
        with open(logPath, 'r') as log:
            newLogSize = log.seek(0, 2)
            log.seek(logSize)
            logSize = newLogSize
            for line in log.read().split("\n"):
                parseLine(line)
        time.sleep(.5)
