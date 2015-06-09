def backtrack(board, pos=0):
    if pos == 81:
        return True
    
    for index in range(pos, 81):
        if board[index] == '.':
            rowStart = index // 9 * 9
            row = board[rowStart:rowStart+9]
            col = board[index % 9:81:9]
            squareStart = (rowStart // 27 * 27) + (index % 9 // 3 * 3)
            square = board[squareStart:squareStart+3] + board[squareStart+9:squareStart+12] + board[squareStart+18:squareStart+21]

            for i in {'1','2','3','4','5','6','7','8','9'} - set(row + col + square):
                board[index] = i
                if backtrack(board,index+1):
                    return True
            board[index] = '.'
            return False
        elif index == 80:
            return True       
    return False
            
if __name__ == "__main__":
    board = list(''.join([input() for i in range(9)]))
    print('\r\n'.join([''.join(board[i:i+9]) for i in range(0, 81, 9)])) if backtrack(board) else print('Unable to find a solution.')
