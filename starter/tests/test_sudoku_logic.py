import pytest

import sudoku_logic


def assert_valid_sudoku(board):
    expected = set(range(1, sudoku_logic.SIZE + 1))
    assert len(board) == sudoku_logic.SIZE
    assert all(len(row) == sudoku_logic.SIZE for row in board)
    assert all(set(row) == expected for row in board)
    assert all(
        {board[row][col] for row in range(sudoku_logic.SIZE)} == expected
        for col in range(sudoku_logic.SIZE)
    )
    for box_row in range(0, sudoku_logic.SIZE, 3):
        for box_col in range(0, sudoku_logic.SIZE, 3):
            box = {
                board[row][col]
                for row in range(box_row, box_row + 3)
                for col in range(box_col, box_col + 3)
            }
            assert box == expected


def test_create_empty_board_has_independent_nine_by_nine_rows():
    board = sudoku_logic.create_empty_board()

    assert len(board) == sudoku_logic.SIZE
    assert all(len(row) == sudoku_logic.SIZE for row in board)
    assert all(value == sudoku_logic.EMPTY for row in board for value in row)
    board[0][0] = 1
    assert board[1][0] == sudoku_logic.EMPTY


@pytest.mark.parametrize(
    ("existing_cell", "expected"),
    [
        (None, True),
        ((0, 4), False),
        ((4, 0), False),
        ((1, 1), False),
    ],
)
def test_is_safe_checks_row_column_and_box(existing_cell, expected):
    board = sudoku_logic.create_empty_board()
    if existing_cell is not None:
        row, col = existing_cell
        board[row][col] = 5

    assert sudoku_logic.is_safe(board, 0, 0, 5) is expected


def test_fill_board_creates_a_valid_sudoku_solution():
    board = sudoku_logic.create_empty_board()

    assert sudoku_logic.fill_board(board) is True
    assert_valid_sudoku(board)


def test_count_solutions_finds_one_solution_for_a_valid_puzzle():
    puzzle = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9],
    ]

    assert sudoku_logic.count_solutions(puzzle) == 1
    assert sudoku_logic.has_unique_solution(puzzle) is True


def test_count_solutions_stops_at_two_for_a_puzzle_with_multiple_solutions():
    puzzle = sudoku_logic.create_empty_board()

    assert sudoku_logic.count_solutions(puzzle) == 2
    assert sudoku_logic.has_unique_solution(puzzle) is False


def test_count_solutions_returns_zero_for_an_unsolvable_puzzle():
    puzzle = sudoku_logic.create_empty_board()
    puzzle[0][0] = 5
    puzzle[0][1] = 5

    assert sudoku_logic.count_solutions(puzzle) == 0
    assert sudoku_logic.has_unique_solution(puzzle) is False


@pytest.mark.parametrize(
    "board",
    [
        [[0] * sudoku_logic.SIZE],
        [[0] * sudoku_logic.SIZE for _ in range(sudoku_logic.SIZE - 1)],
        [[0] * (sudoku_logic.SIZE - 1) for _ in range(sudoku_logic.SIZE)],
        [[True] + [0] * (sudoku_logic.SIZE - 1)]
        + [[0] * sudoku_logic.SIZE for _ in range(sudoku_logic.SIZE - 1)],
        [[10] + [0] * (sudoku_logic.SIZE - 1)]
        + [[0] * sudoku_logic.SIZE for _ in range(sudoku_logic.SIZE - 1)],
    ],
)
def test_count_solutions_rejects_malformed_boards(board):
    with pytest.raises(ValueError):
        sudoku_logic.count_solutions(board)


def test_generated_solution_is_valid_and_matches_puzzle_clues():
    puzzle, solution = sudoku_logic.generate_puzzle()

    assert_valid_sudoku(solution)
    assert len(puzzle) == sudoku_logic.SIZE
    assert all(len(row) == sudoku_logic.SIZE for row in puzzle)
    assert sum(value != 0 for row in puzzle for value in row) == 35
    assert sudoku_logic.has_unique_solution(puzzle) is True
    assert all(
        value == 0 or value == solution[row][col]
        for row, values in enumerate(puzzle)
        for col, value in enumerate(values)
    )
