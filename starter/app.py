from flask import Flask, render_template, jsonify, request
import random
import sudoku_logic

app = Flask(__name__)

# Keep a simple in-memory store for current puzzle and solution
CURRENT = {
    'puzzle': None,
    'solution': None,
    'hints_used': 0,
    'hinted_cells': set(),
    'completed': False,
}

DIFFICULTY_CLUES = {
    'easy': 45,
    'medium': 35,
    'hard': 28,
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/new')
def new_game():
    difficulty = request.args.get('difficulty')
    if difficulty is not None:
        normalized_difficulty = difficulty.strip().lower()
        if normalized_difficulty not in DIFFICULTY_CLUES:
            return jsonify({
                'error': 'Invalid difficulty. Choose Easy, Medium, or Hard.'
            }), 400
        clues = DIFFICULTY_CLUES[normalized_difficulty]
    else:
        clues = int(request.args.get('clues', 35))

    puzzle, solution = sudoku_logic.generate_puzzle(clues)
    CURRENT['puzzle'] = puzzle
    CURRENT['solution'] = solution
    CURRENT['hints_used'] = 0
    CURRENT['hinted_cells'] = set()
    CURRENT['completed'] = False
    return jsonify({'puzzle': puzzle})


def _is_valid_board(board):
    return (
        isinstance(board, list)
        and len(board) == sudoku_logic.SIZE
        and all(
            isinstance(row, list)
            and len(row) == sudoku_logic.SIZE
            and all(
                isinstance(value, int)
                and not isinstance(value, bool)
                and 0 <= value <= sudoku_logic.SIZE
                for value in row
            )
            for row in board
        )
    )


@app.route('/hint', methods=['POST'])
def get_hint():
    puzzle = CURRENT.get('puzzle')
    solution = CURRENT.get('solution')
    if puzzle is None or solution is None:
        return jsonify({'error': 'No game in progress'}), 400
    if CURRENT.get('completed'):
        return jsonify({'error': 'The game is already complete'}), 400

    data = request.get_json(silent=True)
    board = data.get('board') if isinstance(data, dict) else None
    if not _is_valid_board(board):
        return jsonify({'error': 'A valid 9x9 board is required'}), 400

    hinted_cells = CURRENT.setdefault('hinted_cells', set())
    available_cells = [
        (row, col)
        for row in range(sudoku_logic.SIZE)
        for col in range(sudoku_logic.SIZE)
        if puzzle[row][col] == sudoku_logic.EMPTY
        and board[row][col] == sudoku_logic.EMPTY
        and (row, col) not in hinted_cells
    ]
    if not available_cells:
        return jsonify({'error': 'No empty cells remain'}), 400

    row, col = random.choice(available_cells)
    hinted_cells.add((row, col))
    CURRENT['hints_used'] += 1
    return jsonify({
        'row': row,
        'col': col,
        'value': solution[row][col],
        'locked': True,
        'hints_used': CURRENT['hints_used'],
    })


@app.route('/check', methods=['POST'])
def check_solution():
    data = request.get_json(silent=True)
    board = data.get('board') if isinstance(data, dict) else None
    solution = CURRENT.get('solution')
    if solution is None:
        return jsonify({'error': 'No game in progress'}), 400
    if not _is_valid_board(board):
        return jsonify({'error': 'A valid 9x9 board is required'}), 400

    incorrect = []
    for i in range(sudoku_logic.SIZE):
        for j in range(sudoku_logic.SIZE):
            if board[i][j] != solution[i][j]:
                incorrect.append([i, j])
    if not incorrect:
        CURRENT['completed'] = True
    return jsonify({'incorrect': incorrect})

if __name__ == '__main__':
    app.run(debug=True)