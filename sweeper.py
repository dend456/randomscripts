#! /usr/bin/env python3.4
import time, random, ctypes, win32gui, win32con, win32api
from PIL import Image, ImageGrab

x_positions = [186, 237, 289, 341, 392, 444, 496, 547, 599, 651, 703, 754, 806, 858, 909, 962, 1014, 1065, 1117, 1169, 1220, 1272, 1324, 1376,
               1427, 1479, 1531, 1582, 1634, 1686]
y_positions = [129, 180, 232, 284, 335, 387, 439, 491, 542, 595, 647, 698, 750, 802, 853, 905]
colors = [((23, 43), (60, 78, 194)), ((23, 40), (24, 103, 12)), ((21, 26), (173, 16, 12)), ((30, 33), (0, 1, 121)), ((24, 24), (126, 0, 2)),
          ((38, 36), (2, 123, 133)), ((16, 14), (158, 34, 26)),  ((16, 35), (168, 14, 8))]

original_color_offset = 10
board_size = (30, 16)
place_flags = False
play_button_coords = [(1050, 600), (1000, 625)]


def click(cell_x, cell_y, button=1, delay=0.01):
    mouse_pos = win32gui.GetCursorPos()
    ctypes.windll.user32.SetCursorPos(x_positions[cell_x] + 3, y_positions[cell_y] + 3)
    if button == 1:
        ctypes.windll.user32.mouse_event(0x2, 0, 0, 0, 0)
        time.sleep(delay)
        ctypes.windll.user32.mouse_event(0x4, 0, 0, 0, 0)
    elif button == 2:
        ctypes.windll.user32.mouse_event(0x8, 0, 0, 0, 0)
        time.sleep(delay)
        ctypes.windll.user32.mouse_event(0x10, 0, 0, 0, 0)
    ctypes.windll.user32.SetCursorPos(*mouse_pos)


def click_abs(x, y, button=1, delay=0.01):
    mouse_pos = win32gui.GetCursorPos()
    ctypes.windll.user32.SetCursorPos(x, y)
    if button == 1:
        ctypes.windll.user32.mouse_event(0x2, 0, 0, 0, 0)
        time.sleep(delay)
        ctypes.windll.user32.mouse_event(0x4, 0, 0, 0, 0)
    elif button == 2:
        ctypes.windll.user32.mouse_event(0x8, 0, 0, 0, 0)
        time.sleep(delay)
        ctypes.windll.user32.mouse_event(0x10, 0, 0, 0, 0)
    ctypes.windll.user32.SetCursorPos(*mouse_pos)


def count_bombs(x, y, board):
    surrounding_bombs = 0
    min_x = max(0, x-1)
    min_y = max(0, y-1)
    max_x = min(board_size[0]-1, x+1)
    max_y = min(board_size[1]-1, y+1)

    for my in range(min_y, max_y + 1):
        for mx in range(min_x, max_x + 1):
            if board[my][mx] == 'x':
                surrounding_bombs += 1
    return surrounding_bombs


def get_open_space(x, y, board):
    min_x = max(0, x-1)
    min_y = max(0, y-1)
    max_x = min(board_size[0]-1, x+1)
    max_y = min(board_size[1]-1, y+1)

    for my in range(min_y, max_y + 1):
        for mx in range(min_x, max_x + 1):
            if board[my][mx] == ' ':
                return (mx, my)


def fill_bombs(board):
    for y in range(board_size[1]):
        for x in range(board_size[0]):
            bombs = board[y][x]
            if bombs == ' ' or bombs == 'x':
                continue
            surrounding_bombs = 0
            min_x = max(0, x-1)
            min_y = max(0, y-1)
            max_x = min(board_size[0]-1, x+1)
            max_y = min(board_size[1]-1, y+1)
            for my in range(min_y, max_y + 1):
                for mx in range(min_x, max_x + 1):
                    if board[my][mx] == ' ' or board[my][mx] == 'x':
                        surrounding_bombs += 1
            if surrounding_bombs == bombs:
                for my in range(min_y, max_y + 1):
                    for mx in range(min_x, max_x + 1):
                        if board[my][mx] == ' ':
                            board[my][mx] = 'x'
                            if place_flags:
                                click(mx, my, 2)
                                time.sleep(.01)
    return board


def get_board(board, original_colors):
    img = ImageGrab.grab().convert('RGBA')

    for y in range(board_size[1]):
        for x in range(board_size[0]):
            if board[y][x] != ' ':
                continue
            px = x_positions[x] + original_color_offset
            py = y_positions[y] + original_color_offset
            color = img.getpixel((px, py))
            if color == original_colors[y][x]:
                continue
            closest = 0
            closest_val = 30
            for i in range(0, 8):
                px = x_positions[x] + colors[i][0][0]
                py = y_positions[y] + colors[i][0][1]

                color = img.getpixel((px, py))
                diff = abs(color[0] - colors[i][1][0]) + abs(color[1] - colors[i][1][1]) + abs(color[2] - colors[i][1][2])
                if diff < closest_val:
                    closest = i + 1
                    closest_val = diff
            board[y][x] = closest
    return fill_bombs(board)


def print_board(board):
    for row in board:
        print(' '.join([str(i) for i in row]))


def get_move(board):
    for y in range(board_size[1]):
        for x in range(board_size[0]):
            if board[y][x] == ' ' or board[y][x] == 'x':
                continue
            if board[y][x] == count_bombs(x, y, board):
                move = get_open_space(x, y, board)
                if move:
                    return move
    for y in range(board_size[1]):
        for x in range(board_size[0]):
            if board[y][x] == ' ':
                return (x, y)


def main():
    hwnd = win32gui.FindWindow(None, 'Minesweeper')
    win32gui.SetForegroundWindow(hwnd)
    win32gui.SetActiveWindow(hwnd)
    #win32gui.SetFocus(hwnd)
    #ctypes.windll.user32.SetCursorPos(1000, 1000)
    time.sleep(2)

    original_colors = []
    original = ImageGrab.grab().convert('RGBA')

    for y in range(board_size[1]):
        row_colors = []
        for x in range(board_size[0]):
            row_colors.append(original.getpixel((x_positions[x] + original_color_offset, y_positions[y] + original_color_offset)))
        original_colors.append(row_colors)

    running = True

    while running:
        board = [[' '] * board_size[0] for _ in range(board_size[1])]
        x = random.randint(0, board_size[0] - 1)
        y = random.randint(0, board_size[1] - 1)
        click(x, y)
        time.sleep(.3)
        board = get_board(board, original_colors)
        won = False

        while True:
            if win32api.GetAsyncKeyState(win32con.VK_ESCAPE):
                running = False
                break
            elif win32gui.FindWindow(None, 'Game Won'):
                won = True
                break
            elif win32gui.FindWindow(None, 'Game Lost'):
                break

            move = get_move(board)
            click(move[0], move[1])
            time.sleep(.05)
            board = get_board(board, original_colors)

            #print_board(board)
            #print('---')

        if running:
            time.sleep(.2)
            if won:
                click_abs(play_button_coords[1][0], play_button_coords[1][1])
            else:
                click_abs(play_button_coords[0][0], play_button_coords[0][1])
            time.sleep(1.5)

if __name__ == '__main__':
    main()