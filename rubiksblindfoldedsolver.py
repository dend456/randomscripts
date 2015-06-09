algorithms = {'T' : "R U R' U' R' F R2 U' R' U' R U R' F'", 'Y' : "R U' R' U' R U R' F' R U R' U' R' F R", 'Jb': "R U R' F' R U R' U' R' F R2 U' R' U'",'Ja': "F U' R' F R2 U' R' U' R U R' F' R U R' F'",'parity' : "Ja T Ja"}
cornerAlgs = {'B':"R D' Y D R'", 'C':"F Y F'", 'D':"F R' Y R F'", 'F':"F2 Y F2", 'G':"D2 R Y R' D2", 'H':"D2 Y D2", 'I':"F' D Y D' F", 'J':"F2 D Y D' F2", 'K':"F D Y D' F'", 'L':"D Y D'", 'M':"R' Y R", 'N':"R2 Y R2",'O':"R Y R'", 'P':"Y", 'Q':"R' F Y F' R", 'S':"D' R Y R' D", 'T':"D' Y D", 'U':"F' Y F", 'V':"F' R' Y R F", 'W':"R2 F Y F' R2", 'X':"D F' Y F D'"}
edgeAlgs = {'y':'y','z':"z",'a':"Ja", 'c':"Jb", 'd':"T", 'e':"L' U B' U' T U B U' L", 'f':"U' F U T U' F' U", 'g':"D M' Jb M D'", 'h':"U B' U' T U B U'", 'i':"M' Ja M", 'j':"U2 R U2 T U2 R' U2", 'k':"M' Jb M", 'l':"L' T L", 'n':"U B U' T U B' U'", 'o':"D' M' Jb M D", 'p':"U' F' U T U' F U", 'q':"M Jb M'", 'r':"L T L'", 's':"M Ja M'", 't':"U2 R' U2 T U2 R U2", 'u':"M2 Ja M2", 'v':"D2 L2 T L2 D2", 'w':"M2 Jb M2", 'x':"L2 T L2"}
algs = dict(cornerAlgs, **edgeAlgs)


def getCornerPos(colors, centers):
    top = centers['cu'] in colors
    left = centers['cl'] in colors
    front = centers['cf'] in colors

    if top:
        if left:
            if front: return 3
            else: return 0
        else:
            if front: return 2
            else: return 1
    else:
        if left:
            if front: return 4
            else: return 7
        else:
            if front: return 5
            else: return 6


def getEdgePos(colors, centers):
    top = centers['cu'] in colors
    left = centers['cl'] in colors
    front = centers['cf'] in colors
    right = centers['cr'] in colors
    down = centers['cd'] in colors

    if top:
        if left: return 3
        elif right: return 1
        elif front: return 2
        else: return 0
    elif down:
        if left: return 11
        elif right: return 9
        elif front: return 8
        else: return 10
    else:
        if left and front: return 7
        elif left: return 4
        elif front: return 6
        else: return 5


def getCornerStickerLetter(color, cornerPos, centers):
    if cornerPos == 0:
        if color == centers['cu']: return 'A'
        elif color == centers['cl']: return 'E'
        else: return 'R'
    elif cornerPos == 1:
        if color == centers['cu']: return 'B'
        elif color == centers['cr']: return 'N'
        else: return 'Q'
    elif cornerPos == 2:
        if color == centers['cu']: return 'C'
        elif color == centers['cf']: return 'J'
        else: return 'M'
    elif cornerPos == 3:
        if color == centers['cu']: return 'D'
        elif color == centers['cl']: return 'F'
        else: return 'I'
    elif cornerPos == 4:
        if color == centers['cd']: return 'U'
        elif color == centers['cl']: return 'G'
        else: return 'L'
    elif cornerPos == 5:
        if color == centers['cd']: return 'V'
        elif color == centers['cf']: return 'K'
        else: return 'P'
    elif cornerPos == 6:
        if color == centers['cd']: return 'W'
        elif color == centers['cr']: return 'O'
        else: return 'T'
    else:
        if color == centers['cd']: return 'X'
        elif color == centers['cl']: return 'H'
        else: return 'S' 


def getEdgeStickerLetter(color, edgePos, centers):
    if edgePos == 0:
        if color == centers['cu']: return 'a'
        else: return 'q'
    elif edgePos == 1:
        if color == centers['cu']: return 'b'
        else: return 'm'
    elif edgePos == 2:
        if color == centers['cu']: return 'c'
        else: return 'i'
    elif edgePos == 3:
        if color == centers['cu']: return 'd'
        else: return 'e'
    elif edgePos == 4:
        if color == centers['cl']: return 'h'
        else: return 'r'
    elif edgePos == 5:
        if color == centers['cr']: return 'n'
        else: return 't'
    elif edgePos == 6:
        if color == centers['cr']: return 'p'
        else: return 'j'
    elif edgePos == 7:
        if color == centers['cf']: return 'l'
        else: return 'f'
    elif edgePos == 8:
        if color == centers['cd']: return 'u'
        else: return 'k'
    elif edgePos == 9:
        if color == centers['cd']: return 'v'
        else: return 'o'
    elif edgePos == 10:
        if color == centers['cd']: return 'w'
        else: return 's'
    else:
        if color == centers['cd']: return 'x'
        else: return 'g'

def getCornerPosFromLetter(letter):
    if letter in "AER": return 0
    elif letter in "BQN": return 1
    elif letter in "CMJ": return 2
    elif letter in "DIF": return 3
    elif letter in "UGL": return 4
    elif letter in "VKP": return 5
    elif letter in "WOT": return 6
    else: return 7

def getEdgePosFromLetter(letter):
    return "aqbmcidehrntpjflukvowsxg".index(letter) // 2


def getCornerColors(cornerPos, corners):
    return [(corners['A'],corners['E'],corners['R']),(corners['B'],corners['Q'],corners['N']),(corners['C'],corners['M'],corners['J']),(corners['D'],corners['I'],corners['F']),(corners['U'],corners['G'],corners['L']),(corners['V'],corners['K'],corners['P']),(corners['W'],corners['O'],corners['T']),(corners['X'],corners['S'],corners['H'])][cornerPos]


def getEdgeColors(edgePos, edges):
    return [(edges['a'],edges['q']),(edges['b'],edges['m']),(edges['c'],edges['i']),(edges['d'],edges['e']),(edges['h'],edges['r']),(edges['n'],edges['t']),(edges['p'],edges['j']),(edges['f'],edges['l']),(edges['u'],edges['k']),(edges['v'],edges['o']),(edges['w'],edges['s']),(edges['x'],edges['g'])][edgePos]


def getCornerRotation(colors, centers):
    if colors[0] == centers['cu'] or colors[0] == centers['cd']: return 0
    elif colors[1] == centers['cu'] or colors[1] == centers['cd']: return 1
    else: return 2


def getEdgeRotation(colors, centers):
    if colors[0] == centers['cu'] or colors[0] == centers['cl'] or colors[0] == centers['cr'] or colors[0] == centers['cd']: return 0
    else: return 1


def solve(cube):
    solution = []

    corners = dict()
    edges = dict()
    centers = dict()

    for key, value in cube.items():
        if len(key) == 2:
            centers[key] = value
        elif key < 'a':
            corners[key] = value
        else:
            edges[key] = value

    cornerStates = [3] * 8
    edgeStates = [2] * 12

    for i in range(0,8):
        colors = getCornerColors(i,corners)
        pos = getCornerPos(colors, centers)
        if pos == i:
            cornerStates[i] = getCornerRotation(colors, centers)

    for i in range(0,12):
        colors = getEdgeColors(i,edges)
        pos = getEdgePos(colors, centers)
        if pos == i:
            edgeStates[i] = getEdgeRotation(colors, centers)

    currentLetter = ''
    while any(cornerStates):
        if not currentLetter:
            if cornerStates[0] != 0:
                currentLetter = 'A'
            else:
                for i in range(1,8):
                    if cornerStates[i]:
                        colors = getCornerColors(i,corners)
                        letter = ['A','B','C','D','U','V','W','X'][i]
                        newColors = getCornerColors(i, corners)
                        newPos = getCornerPos(colors, centers)
                        currentLetter = getCornerStickerLetter(corners[letter],newPos,centers)
                        solution.append(letter)
                        break

        if currentLetter != 'A':
            solution.append(currentLetter)

        pos = getCornerPosFromLetter(currentLetter)
        cornerStates[pos] = 0

        colors = getCornerColors(pos, corners)
        rotation = cornerStates[pos]
        newPos = getCornerPos(colors, centers)
        if cornerStates[newPos]:
            currentLetter = getCornerStickerLetter(corners[currentLetter], newPos, centers)
        else:
            currentLetter = ''

    if len(solution) % 2 == 1:
        solution.append('z')
    else:
        solution.append('y')

    currentLetter = ''
    while any(edgeStates):
        if not currentLetter:
            if edgeStates[1] != 0:
                currentLetter = 'b'
            else:
                for i in [0] + list(range(2,12)):
                    if edgeStates[i]:
                        colors = getEdgeColors(i,edges)
                        letter = ['a','b','c','d','h','n','p','f','u','v','w','x'][i]
                        newColors = getEdgeColors(i, edges)
                        newPos = getEdgePos(colors, centers)
                        currentLetter = getEdgeStickerLetter(edges[letter],newPos,centers)
                        solution.append(letter)
                        break

        if currentLetter != 'b':
            solution.append(currentLetter)

        pos = getEdgePosFromLetter(currentLetter)
        edgeStates[pos] = 0

        colors = getEdgeColors(pos, edges)
        rotation = edgeStates[pos]
        newPos = getEdgePos(colors, centers)
        if edgeStates[newPos]:
            currentLetter = getEdgeStickerLetter(edges[currentLetter], newPos, centers)
        else:
            currentLetter = ''

    return ''.join(solution)

if __name__ == '__main__':
    keys = ['A','a','B','d','cu','b','D','c','C','E','e','F','h','cl','f','H','g','G','I','i','J','l','cf','j','L','k','K','M','m','N','p','cr','n','P','o','O','Q','q','R','t','cb','r','T','s','S','U','u','V','x','cd','v','X','w','W',]
    cube = dict(zip(keys,list(input())))
    memo = solve(cube)
    print('Memo: {}'.format(memo.lower()))
    simple = '\r\n'.join([algs[x] for x in list(memo)])
    print('Simple solution:\r\n{}'.format(simple))
    print('Expanded solution:\r\n{}'.format(simple.replace('z',algorithms['parity']).replace('Ja',algorithms['Ja']).replace('Jb',algorithms['Jb']).replace('Y',algorithms['Y']).replace('T',algorithms['T'])))
