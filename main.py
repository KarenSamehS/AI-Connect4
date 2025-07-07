import time

import pygame
import sys
import math
import random
from TreeVisualizer import TreeVisualizer

# Constants
ROW_COUNT = 6
COLUMN_COUNT = 7
SQUARESIZE = 100
RADIUS = int(SQUARESIZE / 2 - 7)
WIDTH = COLUMN_COUNT * SQUARESIZE
HEIGHT = (ROW_COUNT + 1) * SQUARESIZE
SCREEN_SIZE = (WIDTH, HEIGHT)

# RGB colors
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)


# used for tree visualization

class TreeNode:
    def __init__(self, move=None, is_max=True, is_chance=False, depth=0, probability=None):
        self.move = move
        self.score = None
        self.is_max = is_max
        self.depth = depth
        self.children = []
        self.best = False
        self.is_chance = is_chance
        self.probability = probability

    def add_child(self, child_node):
        self.children.append(child_node)


def create_board():
    return "0" * (ROW_COUNT * COLUMN_COUNT)


def get_index(row, col):
    return row * COLUMN_COUNT + col


def get_cell(board, row, col):
    return board[get_index(row, col)]


def set_cell(board, row, col, piece):
    idx = get_index(row, col)
    return board[:idx] + str(piece) + board[idx + 1:]


def is_valid_location(board, col):
    top_row_index = get_index(ROW_COUNT - 1, col)
    return board[top_row_index] == '0'


def get_next_open_row(board, col):
    for r in range(ROW_COUNT):
        if get_cell(board, r, col) == '0':
            return r
    return -1  # column full


def draw_board(screen, board, label):
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT):
            pygame.draw.rect(screen, BLUE, (c * SQUARESIZE, (r + 1) * SQUARESIZE, SQUARESIZE, SQUARESIZE))
            pygame.draw.circle(screen, BLACK,
                               (int(c * SQUARESIZE + SQUARESIZE / 2), int((r + 1) * SQUARESIZE + SQUARESIZE / 2)),
                               RADIUS)

    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT):
            cell = get_cell(board, r, c)
            if cell == '1':  # player 1 ---> RED , human
                pygame.draw.circle(screen, RED,
                                   (int(c * SQUARESIZE + SQUARESIZE / 2), HEIGHT - int((r + 0.5) * SQUARESIZE)), RADIUS)
            elif cell == '2':  # player 2 ----> YELLOW , AI
                pygame.draw.circle(screen, YELLOW,
                                   (int(c * SQUARESIZE + SQUARESIZE / 2), HEIGHT - int((r + 0.5) * SQUARESIZE)), RADIUS)

    font = pygame.font.SysFont("monospace", 75)
    score_size = font.size(f"You: 10         AI: 10")
    pygame.draw.rect(screen, BLACK, (40, 10, score_size[0], score_size[1]))

    screen.blit(label, (40, 10))
    pygame.display.update()


def winning_moves(board, piece):
    # this checks any win for the player not specified towards adding this exact piece
    # Check horizontal
    wins = 0
    for r in range(ROW_COUNT):
        for c in range(COLUMN_COUNT - 3):
            if all(get_cell(board, r, c + i) == str(piece) for i in range(4)):
                wins += 1

    # Check vertical
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT - 3):
            if all(get_cell(board, r + i, c) == str(piece) for i in range(4)):
                wins += 1

    # Check positively sloped diagonals
    for r in range(ROW_COUNT - 3):
        for c in range(COLUMN_COUNT - 3):
            if all(get_cell(board, r + i, c + i) == str(piece) for i in range(4)):
                wins += 1

    # Check negatively sloped diagonals
    for r in range(3, ROW_COUNT):
        for c in range(COLUMN_COUNT - 3):
            if all(get_cell(board, r - i, c + i) == str(piece) for i in range(4)):
                wins += 1

    return wins


def evaluate_window(window, piece):
    score = 0
    opp_piece = '1' if piece == '2' else '2'

    # Scoring for AI's pieces
    if window.count(piece) == 4:
        score += 1000  # Win condition
    elif window.count(piece) == 3 and window.count('0') == 1:
        score += 100  # Three-in-a-row with one empty space
    elif window.count(piece) == 2 and window.count('0') == 2:
        score += 10  # Two-in-a-row with two empty spaces

    # Penalties for opponent's pieces
    if window.count(opp_piece) == 4:
        score -= 1100  # Opponent win condition (higher than AI win to prioritize blocking)
    elif window.count(opp_piece) == 3 and window.count('0') == 1:
        score -= 90  # Block opponent's three-in-a-row
    elif window.count(opp_piece) == 2 and window.count('0') == 2:
        score -= 10  # Slight penalty for potential threats

    return score


def score_position(board, piece):
    score = 0

    # Score center column
    center_col = [get_cell(board, r, COLUMN_COUNT // 2) for r in range(ROW_COUNT)]
    center_count = center_col.count(str(piece))
    score += center_count * 3

    # Horizontal
    for r in range(ROW_COUNT):
        row = [get_cell(board, r, c) for c in range(COLUMN_COUNT)]
        for c in range(COLUMN_COUNT - 3):
            window = row[c:c + 4]
            score += evaluate_window(window, str(piece))

    # Vertical
    for c in range(COLUMN_COUNT):
        col = [get_cell(board, r, c) for r in range(ROW_COUNT)]
        for r in range(ROW_COUNT - 3):
            window = col[r:r + 4]
            score += evaluate_window(window, str(piece))

    # Positive diagonal
    for r in range(ROW_COUNT - 3):
        for c in range(COLUMN_COUNT - 3):
            window = [get_cell(board, r + i, c + i) for i in range(4)]
            score += evaluate_window(window, str(piece))

    # Negative diagonal
    for r in range(3, ROW_COUNT):
        for c in range(COLUMN_COUNT - 3):
            window = [get_cell(board, r - i, c + i) for i in range(4)]
            score += evaluate_window(window, str(piece))

    return score


# -------------------- ALGORITHMS----------------------

def get_valid_locations(board):
    return [c for c in range(COLUMN_COUNT) if is_valid_location(board, c)]


def is_terminal_node(board):
    # return winning_move(board, 1) or winning_move(board, 2) or len(get_valid_locations(board)) == 0
    # only terminal when board is full
    return len(get_valid_locations(board)) == 0


def minimax(board, depth, maximizingPlayer, node, stats):  # minimax with no pruning
    valid_locations = get_valid_locations(board)
    is_terminal = is_terminal_node(board)
    if is_terminal:
        human_wins = winning_moves(board, 1)
        ai_wins = winning_moves(board, 2)
        if ai_wins > human_wins:
            score = 100000000000
        elif ai_wins < human_wins:
            score = -100000000000
        else:
            score = 0  # draw
        node.score = score
        return None, score

    if depth == 0:
        score = score_position(board, 2)
        node.score = score
        return None, score
        # depend on the heuristic only
        # with no thinking ahead using the tree logic with higher depths

    best_child = None
    if maximizingPlayer:
        value = -math.inf
        best_col = random.choice(valid_locations)

        for col in valid_locations:
            row = get_next_open_row(board, col)
            new_board = set_cell(board, row, col, 2)

            child_node = TreeNode(move=col, is_max=False, depth=node.depth + 1)
            node.add_child(child_node)
            stats['expanded'] += 1

            new_score = minimax(new_board, depth - 1, False, child_node, stats)[1]
            if new_score > value:
                value = new_score
                best_col = col
                best_child = child_node

        node.score = value
        best_child.best = True
        return best_col, value
    else:
        value = math.inf
        best_col = random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_open_row(board, col)
            new_board = set_cell(board, row, col, 1)

            child_node = TreeNode(move=col, is_max=True, depth=node.depth + 1)
            node.add_child(child_node)
            stats['expanded'] += 1

            new_score = minimax(new_board, depth - 1, True, child_node, stats)[1]
            if new_score < value:
                value = new_score
                best_col = col
                best_child = child_node

        node.score = value
        best_child.best = True
        return best_col, value


def minimaxPruning(board, depth, maximizingPlayer, alpha, beta, node, stats):  # alpha-beta pruning
    valid_locations = get_valid_locations(board)
    is_terminal = is_terminal_node(board)
    if is_terminal:
        human_wins = winning_moves(board, 1)
        ai_wins = winning_moves(board, 2)
        if ai_wins > human_wins:
            score = 100000000000
        elif ai_wins < human_wins:
            score = -100000000000
        else:
            score = 0  # draw
        node.score = score
        return None, score

    if depth == 0:
        score = score_position(board, 2)
        node.score = score
        return None, score

    best_child = None
    if maximizingPlayer:
        value = -math.inf
        best_col = random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_open_row(board, col)
            new_board = set_cell(board, row, col, 2)

            child_node = TreeNode(move=col, is_max=False, depth=node.depth + 1)
            node.add_child(child_node)
            stats['expanded'] += 1

            new_score = minimaxPruning(new_board, depth - 1, False, alpha, beta, child_node, stats)[1]
            if new_score > value:
                value = new_score
                best_col = col
                best_child = child_node
            if value > alpha:
                alpha = value
            if value >= beta:
                break

        best_child.best = True
        node.score = value
        return best_col, value
    else:
        value = math.inf
        best_col = random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_open_row(board, col)
            new_board = set_cell(board, row, col, 1)

            child_node = TreeNode(move=col, is_max=True, depth=node.depth + 1)
            node.add_child(child_node)
            stats['expanded'] += 1

            new_score = minimaxPruning(new_board, depth - 1, True, alpha, beta, child_node, stats)[1]
            if new_score < value:
                value = new_score
                best_col = col
                best_child = child_node
            if value < beta:
                beta = value
            if value <= alpha:
                break

        best_child.best = True
        node.score = value
        return best_col, value


def expectiminimax(board, depth, player_type, node, stats, alpha=-math.inf, beta=math.inf):
    valid_locations = get_valid_locations(board)
    is_terminal = is_terminal_node(board)

    # Terminal node check
    if is_terminal:
        ai_wins = winning_moves(board, 2)
        human_wins = winning_moves(board, 1)
        score = 1e12 if ai_wins > human_wins else -1e12 if human_wins > ai_wins else 0
        node.score = score
        return None, score

    if depth == 0:
        score = score_position(board, 2)
        node.score = score
        return None, score

    if player_type == "MAX":
        value = -math.inf
        best_col = random.choice(valid_locations) if valid_locations else None
        best_child = None

        for col in valid_locations:
            # Create child node
            child_node = TreeNode(move=col, is_max=False, is_chance=True, depth=node.depth + 1)
            node.add_child(child_node)
            stats['expanded'] += 1

            # Simulate move
            row = get_next_open_row(board, col)
            new_board = set_cell(board, row, col, 2)

            # Next layer is CHANCE
            _, new_score = expectiminimax(new_board, depth - 1, "CHANCE", child_node, stats, alpha, beta)

            if new_score > value:
                value = new_score
                best_col = col
                best_child = child_node

            alpha = max(alpha, value)
            if alpha >= beta:
                break

        if best_child:  # Only mark if we found a valid move
            best_child.best = True
        node.score = value
        return best_col, value

    elif player_type == "MIN":
        value = math.inf
        best_col = random.choice(valid_locations) if valid_locations else None
        best_child = None

        for col in valid_locations:
            # Create child node
            child_node = TreeNode(move=col, is_max=True, is_chance=True, depth=node.depth + 1)
            node.add_child(child_node)
            stats['expanded'] += 1

            # Simulate move
            row = get_next_open_row(board, col)
            new_board = set_cell(board, row, col, 1)

            # Next layer is CHANCE
            _, new_score = expectiminimax(new_board, depth - 1, "CHANCE", child_node, stats, alpha, beta)

            if new_score < value:
                value = new_score
                best_col = col
                best_child = child_node

            beta = min(beta, value)
            if beta <= alpha:
                break

        if best_child:
            best_child.best = True
        node.score = value
        return best_col, value

    elif player_type == "CHANCE":
        expected_value = 0
        chance_outcomes = [
            (0, 0.6),  # 60% chance: move succeeds as intended
            (-1, 0.2),  # 20% chance: move shifts left
            (1, 0.2)  # 20% chance: move shifts right
        ]

        for col in valid_locations:
            # chance wrapper node is distinguished with is_max is None as the next nodes will be chance nodes
            chance_wrapper = TreeNode(move=col, is_max=None, is_chance=True, depth=node.depth + 1)
            node.add_child(chance_wrapper)
            for offset, prob in chance_outcomes:
                modified_col = col + offset
                if 0 <= modified_col < COLUMN_COUNT:  # Check bounds properly
                    # Create chance node
                    chance_node = TreeNode(
                        move=modified_col,
                        is_max=node.is_max,  # is_max is set according to next player after chance node
                        depth=chance_wrapper.depth + 1,
                        probability=prob
                    )
                    chance_wrapper.add_child(chance_node)
                    # stats['chance']+=1

                    # Simulate move
                    row = get_next_open_row(board, modified_col)
                    new_board = set_cell(board, row, modified_col, 2 if node.is_max else 1)

                    # Next player is the opponent
                    next_player = "MIN" if node.is_max else "MAX"
                    _, outcome_score = expectiminimax(new_board, depth - 1, next_player, chance_node, stats, alpha,
                                                      beta)

                    expected_value += prob * outcome_score

        node.score = expected_value
        return None, expected_value


def get_depth_input(screen):
    input_active = True
    user_text = ""

    input_rect = pygame.Rect(50, 100, 300, 50)
    color_active = pygame.Color('dodgerblue')
    color_inactive = pygame.Color('lightskyblue3')
    color = color_inactive
    font = pygame.font.SysFont("monospace", 20)
    while input_active:
        screen.fill(BLACK)
        prompt = font.render("Enter Depth :", True, (255, 255, 255))
        screen.blit(prompt, (50, 50))

        # Draw input box
        pygame.draw.rect(screen, color, input_rect, 2)
        text_surface = font.render(user_text, True, (255, 255, 255))
        screen.blit(text_surface, (input_rect.x + 10, input_rect.y + 10))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_rect.collidepoint(event.pos):
                    color = color_active
                else:
                    color = color_inactive
            if event.type == pygame.KEYDOWN:
                if color == color_active:
                    if event.key == pygame.K_RETURN:  # Enter key
                        return int(user_text)

                    elif event.key == pygame.K_BACKSPACE:
                        user_text = user_text[:-1]  # Remove last character
                    else:
                        user_text += event.unicode  # Add character


def get_algorithm_choice(screen):
    # Button positions and sizes
    font = pygame.font.SysFont("monospace", 20)
    minimax_button = pygame.Rect(50, 100, 400, 50)
    alphabeta_button = pygame.Rect(50, 200, 400, 50)
    expectiminimax_button = pygame.Rect(50, 300, 400, 50)

    while True:
        screen.fill(BLACK)
        title = font.render("Choose Algorithm:", True, (255, 255, 255))
        screen.blit(title, (50, 50))

        # Draw buttons
        pygame.draw.rect(screen, (0, 128, 255), minimax_button)
        pygame.draw.rect(screen, (0, 200, 128), alphabeta_button)
        pygame.draw.rect(screen, (255, 128, 0), expectiminimax_button)

        # Button labels
        minimax_label = font.render("Minimax", True, (255, 255, 255))
        alphabeta_label = font.render("Minimax Alpha-Beta", True, (255, 255, 255))
        expectiminimax_label = font.render("ExpectiMinimax", True, (255, 255, 255))
        screen.blit(minimax_label, (minimax_button.x + 50, minimax_button.y + 10))
        screen.blit(alphabeta_label, (alphabeta_button.x + 10, alphabeta_button.y + 10))
        screen.blit(expectiminimax_label, (expectiminimax_button.x + 30, expectiminimax_button.y + 10))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if minimax_button.collidepoint(event.pos):
                    return 1
                elif alphabeta_button.collidepoint(event.pos):
                    return 2
                elif expectiminimax_button.collidepoint(event.pos):
                    return 3


# tree hierarchical visualization in console
def print_tree(node, indent="", last=True):
    if not node.is_chance:
        player = 'MAX' if node.is_max else 'MIN'
    else:
        player = 'Chance'
    # Current node
    prefix = "    " if last else "|   "
    connector = "+-- " if last else "|-- "
    print(f"{indent}{connector}", end="")
    
    prob = ""
    if not node.is_chance and node.probability is not None:
        prob = node.probability
    best = ""
    if node.best:
        best = "**"

    if node.is_chance and node.is_max is None:
        player = 'CHANCE WRAPPER'

    print(f"{player} Move={node.move}, Score={node.score}, depth={node.depth}    {prob}      {best}")

    # Children
    indent += prefix
    for i, child in enumerate(node.children):
        print_tree(child, indent, i == len(node.children) - 1)


def print_time_taken(elapsed_time, algo):
    if algo == 1:
        print(f"MinMax took {elapsed_time:.4f} seconds")
    elif algo == 2:
        print(f"MinMax with pruning took {elapsed_time:.4f} seconds")
    elif algo == 3:
        print(f"ExpectMinMax with pruning took {elapsed_time:.4f} seconds")
    else:
        return
    print("---------------------")


def main():
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption("Connect 4 (String Board)")
    board = create_board()

    font = pygame.font.SysFont("monospace", 75)
    algorithm = get_algorithm_choice(screen)
    depth = get_depth_input(screen)
    label = font.render(("You: 0" + "     AI: 0"), 1, (255, 255, 255))
    draw_board(screen, board, label)
    game_over = False
    turn = 0  # 0 = Human (Player 1), 1 = AI (Player 2)

    while not game_over:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            if event.type == pygame.MOUSEMOTION:
                pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, SQUARESIZE))
                posx = event.pos[0]
                color = RED if turn == 0 else YELLOW
                pygame.draw.circle(screen, color, (posx, int(SQUARESIZE / 2)), RADIUS)
                pygame.display.update()

            if event.type == pygame.MOUSEBUTTONDOWN and turn == 0:  # Human's turn
                pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, SQUARESIZE))
                posx = event.pos[0]
                col = int(posx // SQUARESIZE)

                if is_valid_location(board, col):
                    row = get_next_open_row(board, col)
                    board = set_cell(board, row, col, 1 if turn == 0 else 2)
                    human_wins = winning_moves(board, 1)
                    ai_wins = winning_moves(board, 2)
                    label = font.render(("You:" + str(human_wins) + "     AI:" + str(ai_wins)), 1, (255, 255, 255))
                    draw_board(screen, board, label)

                    # screen.blit(label, (40, 10))
                    # pygame.display.update()
                    # Check if board is full
                    if '0' not in board:  # If no empty spaces, the board is full
                        ai_wins = winning_moves(board, 2)
                        human_wins = winning_moves(board, 1)
                        print("ai" + str(ai_wins))
                        print("human" + str(human_wins))
                        if (ai_wins == human_wins):
                            label = font.render(("Draw!" + str(ai_wins) + "                         "), 1,
                                                (255, 255, 255))
                        elif (ai_wins > human_wins):
                            label = font.render(("AI wins!" + str(ai_wins) + "                         "), 1,
                                                (255, 255, 255))
                        else:
                            label = font.render(("You win!" + str(human_wins) + "                         "), 1,
                                                (255, 255, 255))

                        screen.blit(label, (40, 10))
                        pygame.display.update()
                        pygame.time.wait(10000)
                        game_over = True
                    else:
                        turn ^= 1  # Switch turn

            if not game_over and turn == 1:  # AI's turn (Player 2)
                pygame.time.wait(500)  # Give a small delay for AI to think
                root = TreeNode(is_max=True)
                start_time = time.perf_counter()

                if algorithm == 1:
                    stats = {'expanded': 0}
                    col, _ = minimax(board, depth, True, root, stats)  # Minimax for AI move
                    end_time = time.perf_counter()
                    elapsed_time = end_time - start_time
                    print_time_taken(elapsed_time, 1)
                    print("Nodes expanded:", stats['expanded'] + 1)
                    app = TreeVisualizer()
                    app.draw_tree(root)
                    app.mainloop()

                elif algorithm == 2:
                    stats = {'expanded': 0}
                    col, _ = minimaxPruning(board, depth, True, -math.inf, math.inf, root, stats)  # Minimax for AI move
                    end_time = time.perf_counter()
                    elapsed_time = end_time - start_time
                    print_time_taken(elapsed_time, 2)
                    print("Nodes expanded:", stats['expanded'] + 1)
                    app = TreeVisualizer()
                    app.draw_tree(root)
                    app.mainloop()
                    #app = TreeVisualizer()
                    #app.draw_tree(root)
                    #app.mainloop()

                elif algorithm == 3:
                    stats = {'expanded': 0}
                    # stats = {'expanded': 0, 'chance': 0}
                    col, _ = expectiminimax(board, depth, "MAX", root, stats)
                    end_time = time.perf_counter()
                    elapsed_time = end_time - start_time
                    print_time_taken(elapsed_time, 3)
                    print("Nodes expanded:", stats['expanded'] + 1)
                    # print(f"Nodes expanded: {stats['expanded'] + 1} and chance nodes expanded = {stats['chance']}")
                    app = TreeVisualizer()
                    app.draw_tree(root)
                    app.mainloop()

                print_tree(root)
                print("===========================")

                if is_valid_location(board, col):
                    row = get_next_open_row(board, col)
                    board = set_cell(board, row, col, 2)  # AI is Player 2

                human_wins = winning_moves(board, 1)
                ai_wins = winning_moves(board, 2)
                label = font.render(("You:" + str(human_wins) + "     AI:" + str(ai_wins)), 1, (255, 255, 255))
                draw_board(screen, board, label)
                # screen.blit(label, (40, 10))
                # pygame.display.update()
                if '0' not in board:  # Check if the board is full
                    ai_wins = winning_moves(board, 2)
                    human_wins = winning_moves(board, 1)
                    print("Ai : " + str(ai_wins))
                    print("Human : " + str(human_wins))
                    if (ai_wins == human_wins):
                        label = font.render(("Draw!" + str(ai_wins) + "                         "), 1, (255, 255, 255))
                    elif (ai_wins > human_wins):
                        label = font.render(("AI wins!" + str(ai_wins) + "                         "), 1,
                                            (255, 255, 255))
                    else:
                        label = font.render(("You win!" + str(human_wins) + "                         "), 1,
                                            (255, 255, 255))
                    score_size = font.size(f"You: ({human_wins})         AI: ({ai_wins})")
                    pygame.draw.rect(screen, BLACK, (40, 10, score_size[0], score_size[1]))

                    screen.blit(label, (40, 10))
                    pygame.display.update()
                    pygame.time.wait(10000)
                    game_over = True
                else:
                    turn ^= 1  # Switch to human's turn


if __name__ == "__main__":
    main()
