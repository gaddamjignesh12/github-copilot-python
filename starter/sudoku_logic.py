import copy
import random

SIZE = 9
EMPTY = 0
_FULL_MASK = (1 << (SIZE + 1)) - 2


def deep_copy(board):
    return copy.deepcopy(board)


def create_empty_board():
    return [[EMPTY for _ in range(SIZE)] for _ in range(SIZE)]


def is_safe(board, row, col, num):
    # Check row and column
    for x in range(SIZE):
        if board[row][x] == num or board[x][col] == num:
            return False
    # Check 3x3 box
    start_row = row - row % 3
    start_col = col - col % 3
    for i in range(3):
        for j in range(3):
            if board[start_row + i][start_col + j] == num:
                return False
    return True


def fill_board(board):
    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] == EMPTY:
                possible = list(range(1, SIZE + 1))
                random.shuffle(possible)
                for candidate in possible:
                    if is_safe(board, row, col, candidate):
                        board[row][col] = candidate
                        if fill_board(board):
                            return True
                        board[row][col] = EMPTY
                return False
    return True


def count_solutions(board):
    """Return the number of solutions, capped at two.

    The board must be a 9x9 sequence containing integers from 0 to 9.
    Conflicting clues are treated as an unsolvable board and return zero.
    """
    if not isinstance(board, (list, tuple)) or len(board) != SIZE:
        raise ValueError("A Sudoku board must have 9 rows.")

    working_board = []
    row_masks = [0] * SIZE
    column_masks = [0] * SIZE
    box_masks = [0] * SIZE

    for row_index, row in enumerate(board):
        if not isinstance(row, (list, tuple)) or len(row) != SIZE:
            raise ValueError("Each Sudoku row must have 9 cells.")
        working_row = list(row)
        working_board.append(working_row)
        for column_index, value in enumerate(working_row):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError("Sudoku cells must be integers from 0 to 9.")
            if value < EMPTY or value > SIZE:
                raise ValueError("Sudoku cells must be integers from 0 to 9.")
            if value == EMPTY:
                continue

            bit = 1 << value
            box_index = (row_index // 3) * 3 + column_index // 3
            if (
                row_masks[row_index] & bit
                or column_masks[column_index] & bit
                or box_masks[box_index] & bit
            ):
                return 0
            row_masks[row_index] |= bit
            column_masks[column_index] |= bit
            box_masks[box_index] |= bit

    def search():
        best_row = -1
        best_column = -1
        best_candidates = 0
        fewest_candidates = SIZE + 1

        for row_index in range(SIZE):
            for column_index in range(SIZE):
                if working_board[row_index][column_index] != EMPTY:
                    continue
                box_index = (row_index // 3) * 3 + column_index // 3
                candidates = _FULL_MASK & ~(
                    row_masks[row_index]
                    | column_masks[column_index]
                    | box_masks[box_index]
                )
                candidate_count = bin(candidates).count("1")
                if candidate_count == 0:
                    return 0
                if candidate_count < fewest_candidates:
                    best_row = row_index
                    best_column = column_index
                    best_candidates = candidates
                    fewest_candidates = candidate_count

        if best_row == -1:
            return 1

        box_index = (best_row // 3) * 3 + best_column // 3
        solution_count = 0
        while best_candidates:
            bit = best_candidates & -best_candidates
            best_candidates ^= bit
            value = bit.bit_length() - 1
            working_board[best_row][best_column] = value
            row_masks[best_row] |= bit
            column_masks[best_column] |= bit
            box_masks[box_index] |= bit

            solution_count += search()

            working_board[best_row][best_column] = EMPTY
            row_masks[best_row] &= ~bit
            column_masks[best_column] &= ~bit
            box_masks[box_index] &= ~bit
            if solution_count > 1:
                return 2
        return solution_count

    return search()


def has_unique_solution(board):
    return count_solutions(board) == 1


def remove_cells(board, clues):
    attempts = SIZE * SIZE - clues
    while attempts > 0:
        row = random.randrange(SIZE)
        col = random.randrange(SIZE)
        if board[row][col] != EMPTY:
            board[row][col] = EMPTY
            attempts -= 1


def generate_puzzle(clues=35):
    if isinstance(clues, bool) or not isinstance(clues, int):
        raise ValueError("The clue count must be an integer.")
    if clues < 17 or clues > SIZE * SIZE:
        raise ValueError("The clue count must be between 17 and 81.")

    while True:
        solution = create_empty_board()
        if not fill_board(solution):
            raise RuntimeError("Unable to generate a complete Sudoku solution.")

        puzzle = deep_copy(solution)
        cells = [
            (row, column)
            for row in range(SIZE)
            for column in range(SIZE)
        ]
        random.shuffle(cells)
        clue_count = SIZE * SIZE

        for row, column in cells:
            if clue_count == clues:
                break
            value = puzzle[row][column]
            puzzle[row][column] = EMPTY
            if has_unique_solution(puzzle):
                clue_count -= 1
            else:
                puzzle[row][column] = value

        if clue_count == clues:
            return puzzle, solution
