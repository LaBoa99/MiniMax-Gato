import math
import os
import sys
from enum import Enum

import pygame

# Configuración
script_dir = os.path.dirname(__file__)
pygame.init()
fps = 60
clock = pygame.time.Clock()

WIDTH, HEIHGT = (320, 320)
screen = pygame.display.set_mode((WIDTH, HEIHGT))

# Enums
class COSTS(Enum):
    WIN = 1
    DRAW = 0
    LOST = -1

class PLAYERS(Enum):
    ONE = "X"
    TWO = "O"
    EMPTY = None
    
# Clases
class Symbol(pygame.sprite.Sprite):
    def __init__(self, key, *groups: pygame.sprite.Group) -> None:
        super().__init__(*groups)
        self.image = pygame.image.load(os.path.join(script_dir, "images", f"{key.lower()}.png"))
        self.image = pygame.transform.scale(self.image, (WIDTH // 4, HEIHGT // 4)).convert_alpha()
        self.rect = self.image.get_rect()

class Player(pygame.sprite.Group):
    def __init__(self, key: PLAYERS) -> None:
        super().__init__()
        self.key = key
    
    def get_symbol(self, row, col, board_w_cell, board_h_cell):
        symbol = Symbol(self.key.value)
        offset_center_x, offset_board_y = (board_w_cell // 2), (board_h_cell // 2)
        symbol.rect.center = board_w_cell * row + offset_center_x, board_h_cell * col + offset_board_y
        return symbol
   
class Board():
    def __init__(self) -> None:
        self.board = [[PLAYERS.EMPTY for _ in range(3)] for _ in range(3)]
        self.symbols = [None for _ in range(3 * 3)]
        self.w_box, self.h_box = WIDTH // 3, HEIHGT // 3
        self.empty_cells = 3 * 3
        self.movements = []
        
    def draw(self, screen: pygame.Surface):
        for i in range(1, 3):
            x, y = self.w_box * i, self.h_box * i
            # | lineas verticales
            pygame.draw.line(screen, (0, 0, 0), (x, 0), (x, HEIHGT))
            # --- Lineas horizontales
            pygame.draw.line(screen, (0, 0, 0), (0, y), (WIDTH, y))
            
        for symbol in self.symbols:
            if symbol == None: 
                continue
            screen.blit(symbol.image, symbol.rect)
            
    def clean(self):
        self.empty_cells = 3 * 3
        self.board = [[PLAYERS.EMPTY for _ in range(3)] for _ in range(3)]
        self.symbols = [None for _ in range(3 * 3)]
    
    # Retorna en ganador y el perdedor
    def getWinner(self):
        if self.checkWinner(PLAYERS.ONE) == COSTS.WIN:
            return PLAYERS.ONE, PLAYERS.TWO
        if self.checkWinner(PLAYERS.TWO) == COSTS.WIN:
            return PLAYERS.TWO, PLAYERS.ONE
        return COSTS.DRAW, PLAYERS.EMPTY
    
    def checkWinner(self, player: PLAYERS) -> COSTS:
        # Verificar lineas
        for row in self.board:
            if all(cell == player for cell in row):
                return COSTS.WIN
        
        for col in range(3):
            if all(self.board[row][col] == player for row in range(3)):
                return COSTS.WIN
        
        if all(self.board[i][i] == player for i in range(3)):
            return COSTS.WIN
        
        if all(self.board[i][2 - i] == player for i in range(3)):
            return COSTS.WIN

        return COSTS.DRAW
    
    def insert(self, row: int, col: int, player: Player) -> bool:
        if self.board[row][col] == PLAYERS.EMPTY:
            self.board[row][col] = player.key
            self.empty_cells -= 1
            self.movements.append((row, col, player))
            symbol = player.get_symbol(row, col, self.w_box, self.h_box)
            self.symbols[self.__rowColToIndex(row, col)]= symbol
            return True
        return False

    def get_board(self):
        return [row[:] for row in self.board]
    
    def is_gameover(self):
        return self.empty_cells <= 0

    def count_empty_cells(self):
        count = 0
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == PLAYERS.EMPTY:
                    count += 1
        return count

    def __rowColToIndex(self, row, col, n_cols=3):
        return row * n_cols + col

    # Retorna al jugador que sigue de tirar
    def undo(self):
        last_movement = self.movements.pop()
        row, col, player = last_movement
        self.board[row][col] = PLAYERS.EMPTY
        self.symbols[self.__rowColToIndex(row, col)] = None
        self.empty_cells += 1
        return player   

     
class PlayerIA(Player):
    def __init__(self, key: PLAYERS, opponent: Player) -> None:
        super().__init__(key)
        self.opponent = opponent
        self.board = Board()
        
    def play(self, game):
        self.__updateBoard(game)
        if self.board.is_gameover():
            return
        row, col = self.__bestMovement(self.board)
        return row, col
        
    def __updateBoard(self, game: Board):
        self.board = self.__genGameCopy(game)
    
    def __genGameCopy(self, game: Board):
        gameCopy = Board()
        gameCopy.board = game.get_board()
        gameCopy.empty_cells = game.empty_cells
        return gameCopy
        
    def minimax(self, board: Board, depth: int, is_maximizing: bool):
        if board.is_gameover() or depth == 0:
            winner, loser = board.getWinner()
            if winner == self.key:
                return 1
            elif loser == self.key:
                return -1
            else:
                return 0
        if is_maximizing:
            best_score = -math.inf
            for row in range(3):
                for col in range(3):
                    if board.board[row][col] == PLAYERS.EMPTY:
                        board.insert(row, col, self)
                        new_state = self.__genGameCopy(board)
                        score = self.minimax(new_state, depth - 1, False)
                        board.undo()
                        best_score = max(score, best_score)
            return best_score
        else:
            best_score = math.inf
            for row in range(3):
                for col in range(3):
                    if board.board[row][col] == PLAYERS.EMPTY:
                        board.insert(row, col, self.opponent)
                        new_state = self.__genGameCopy(board)
                        score = self.minimax(new_state, depth - 1, True)
                        board.undo()
                        best_score = min(score, best_score)
            return best_score
    
    def __bestMovement(self, game):
        movements = []
        best_move = None
        best_score = -math.inf
        for row in range(3):
            for col in range(3):
                print(row, col)
                if game.board[row][col] == PLAYERS.EMPTY:
                    game.insert(row, col, self)
                    new_state = self.__genGameCopy(game)
                    score = self.minimax(new_state, 3, True)  # Ajusta la profundidad aquí
                    print('=>', score, row, col)
                    game.undo()
                    if best_score <= score:
                        movements.append([row, col, score])
                        best_score = score
                        best_move = (row, col)
        print(best_move, movements)
        return best_move
                
board = Board()
player = Player(PLAYERS.ONE)
PLAYING_IA = True
player2 = PlayerIA(PLAYERS.TWO, player) if PlayerIA else Player(PLAYERS.TWO)
current_player = PLAYERS.ONE

def make_movement(row, col, current_player):
    row = row if row < 3 else 2 # posible offset de moouse pos 
    col = col if col < 3 else 2 # posible offset de moouse pos 
    wasInserted = board.insert(row, col, player if current_player == PLAYERS.ONE else player2)
    return wasInserted

def have_win(wasInserted, current_player):
    if wasInserted:
        if board.empty_cells < 5 and board.empty_cells  > 0:
            win = board.checkWinner(current_player)
            if win == COSTS.WIN:
                print("GANASTE", current_player)
                board.clean()
        elif board.empty_cells <= 0:
            print("EMPATE")
            board.clean()
    return PLAYERS.TWO if current_player == PLAYERS.ONE else PLAYERS.ONE

while True:
    screen.fill((255, 255, 255))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                row, col = mouse_x // board.w_box, mouse_y // board.h_box
                current_player = have_win(make_movement(row, col, current_player), current_player)
                if PLAYING_IA and current_player == PLAYERS.TWO:
                    row, col = player2.play(board)
                    current_player = have_win(make_movement(row, col, current_player), current_player)
    
    # Draw
    board.draw(screen)
    player.draw(screen)
    player2.draw(screen)
    
    # Final
    pygame.display.flip()
    clock.tick(fps)
