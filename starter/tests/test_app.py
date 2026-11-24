import pytest

import app as sudoku_app


VALID_SOLUTION = [
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9],
]


@pytest.fixture
def client():
    sudoku_app.app.config.update(TESTING=True)
    sudoku_app.CURRENT.update(
        puzzle=None,
        solution=None,
        hints_used=0,
        hinted_cells=set(),
        completed=False,
    )
    with sudoku_app.app.test_client() as test_client:
        yield test_client
    sudoku_app.CURRENT.update(
        puzzle=None,
        solution=None,
        hints_used=0,
        hinted_cells=set(),
        completed=False,
    )


def test_home_page_renders_sudoku_game(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Sudoku Game" in response.data
    assert b"sudoku-board" in response.data
    assert b'id="difficulty"' in response.data


def test_home_page_renders_leaderboard_and_player_name_form(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Top 10 Fastest Times" in response.data
    assert b'id="leaderboard-empty"' in response.data
    assert b'id="player-name"' in response.data


def test_theme_toggle_supports_system_preference_and_saved_selection(client):
    page = client.get("/")
    script = client.get("/static/main.js").get_data(as_text=True)
    styles = client.get("/static/styles.css").get_data(as_text=True)

    assert b'id="theme-toggle"' in page.data
    assert 'const THEME_STORAGE_KEY = \'sudokuTheme\';' in script
    assert 'localStorage.getItem(THEME_STORAGE_KEY)' in script
    assert 'localStorage.setItem(THEME_STORAGE_KEY, nextTheme)' in script
    assert "prefers-color-scheme: dark" in script
    assert '--page-background:' in styles
    assert ':root[data-theme="dark"]' in styles
    assert '.sudoku-cell.incorrect' in styles
    assert '.sudoku-cell.hinted' in styles


def test_leaderboard_uses_browser_storage_and_caps_scores(client):
    response = client.get("/static/main.js")
    script = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "localStorage.getItem" in script
    assert "localStorage.setItem" in script
    assert "const MAX_LEADERBOARD_ENTRIES = 10;" in script


def test_new_endpoint_returns_a_nine_by_nine_puzzle(client):
    response = client.get("/new")

    assert response.status_code == 200
    puzzle = response.get_json()["puzzle"]
    assert len(puzzle) == 9
    assert all(len(row) == 9 for row in puzzle)
    assert all(
        isinstance(value, int) and 0 <= value <= 9
        for row in puzzle
        for value in row
    )
    assert sum(value != 0 for row in puzzle for value in row) == 35


@pytest.mark.parametrize(
    ("difficulty", "expected_clues"),
    [("easy", 45), ("medium", 35), ("hard", 28)],
)
def test_new_endpoint_generates_unique_puzzles_for_each_difficulty(
    client, difficulty, expected_clues
):
    response = client.get("/new", query_string={"difficulty": difficulty})

    assert response.status_code == 200
    puzzle = response.get_json()["puzzle"]
    assert sum(value != 0 for row in puzzle for value in row) == expected_clues
    assert sudoku_app.sudoku_logic.has_unique_solution(puzzle) is True


def test_new_endpoint_rejects_invalid_difficulty(client):
    response = client.get("/new", query_string={"difficulty": "expert"})

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "Invalid difficulty. Choose Easy, Medium, or Hard."
    }


def test_new_endpoint_preserves_legacy_clue_count_parameter(client):
    response = client.get("/new", query_string={"clues": 40})

    assert response.status_code == 200
    puzzle = response.get_json()["puzzle"]
    assert sum(value != 0 for row in puzzle for value in row) == 40


def test_check_endpoint_reports_no_game_in_progress(client):
    response = client.post("/check", json={"board": VALID_SOLUTION})

    assert response.status_code == 400
    assert response.get_json() == {"error": "No game in progress"}


def test_check_endpoint_reports_incorrect_cells(client, monkeypatch):
    puzzle = [[0 for _ in range(9)] for _ in range(9)]
    monkeypatch.setattr(
        sudoku_app.sudoku_logic,
        "generate_puzzle",
        lambda clues: (puzzle, VALID_SOLUTION),
    )
    client.get("/new")

    correct_response = client.post("/check", json={"board": VALID_SOLUTION})
    assert correct_response.status_code == 200
    assert correct_response.get_json() == {"incorrect": []}

    submitted_board = [row[:] for row in VALID_SOLUTION]
    submitted_board[0][0] = 0

    response = client.post("/check", json={"board": submitted_board})

    assert response.status_code == 200
    assert response.get_json() == {"incorrect": [[0, 0]]}


def test_hint_endpoint_returns_the_solution_value_for_an_empty_cell(
    client, monkeypatch
):
    puzzle = [row[:] for row in VALID_SOLUTION]
    puzzle[0][0] = 0
    monkeypatch.setattr(
        sudoku_app.sudoku_logic,
        "generate_puzzle",
        lambda clues: (puzzle, VALID_SOLUTION),
    )
    client.get("/new")

    response = client.post("/hint", json={"board": [row[:] for row in puzzle]})

    assert response.status_code == 200
    hint = response.get_json()
    assert (hint["row"], hint["col"]) == (0, 0)
    assert hint["value"] == VALID_SOLUTION[hint["row"]][hint["col"]]
    assert hint["locked"] is True
    assert hint["hints_used"] == 1
    assert (hint["row"], hint["col"]) in sudoku_app.CURRENT["hinted_cells"]


def test_hint_endpoint_does_not_overwrite_player_entries_or_repeat_hints(
    client, monkeypatch
):
    puzzle = [row[:] for row in VALID_SOLUTION]
    puzzle[0][0] = 0
    puzzle[0][1] = 0
    puzzle[0][2] = 0
    monkeypatch.setattr(
        sudoku_app.sudoku_logic,
        "generate_puzzle",
        lambda clues: (puzzle, VALID_SOLUTION),
    )
    client.get("/new")
    board = [row[:] for row in puzzle]
    board[0][1] = 9

    first_hint = client.post("/hint", json={"board": board}).get_json()
    board[first_hint["row"]][first_hint["col"]] = first_hint["value"]
    second_hint_response = client.post("/hint", json={"board": board})
    second_hint = second_hint_response.get_json()

    assert second_hint_response.status_code == 200
    assert (first_hint["row"], first_hint["col"]) != (0, 1)
    assert (second_hint["row"], second_hint["col"]) != (
        first_hint["row"],
        first_hint["col"],
    )
    assert first_hint["value"] == VALID_SOLUTION[first_hint["row"]][first_hint["col"]]
    assert second_hint["value"] == VALID_SOLUTION[second_hint["row"]][second_hint["col"]]
    assert board[0][1] == 9
    assert second_hint["hints_used"] == 2


def test_hint_endpoint_handles_games_with_no_empty_cells(client, monkeypatch):
    monkeypatch.setattr(
        sudoku_app.sudoku_logic,
        "generate_puzzle",
        lambda clues: (VALID_SOLUTION, VALID_SOLUTION),
    )
    client.get("/new")

    response = client.post("/hint", json={"board": VALID_SOLUTION})

    assert response.status_code == 400
    assert response.get_json() == {"error": "No empty cells remain"}


def test_new_game_resets_the_hint_count(client, monkeypatch):
    puzzle = [row[:] for row in VALID_SOLUTION]
    puzzle[0][0] = 0
    monkeypatch.setattr(
        sudoku_app.sudoku_logic,
        "generate_puzzle",
        lambda clues: (puzzle, VALID_SOLUTION),
    )
    client.get("/new")
    client.post("/hint", json={"board": [row[:] for row in puzzle]})

    client.get("/new")

    assert sudoku_app.CURRENT["hints_used"] == 0
    assert sudoku_app.CURRENT["hinted_cells"] == set()


def test_check_endpoint_completes_only_a_correct_filled_board(client, monkeypatch):
    puzzle = [row[:] for row in VALID_SOLUTION]
    puzzle[0][0] = 0
    monkeypatch.setattr(
        sudoku_app.sudoku_logic,
        "generate_puzzle",
        lambda clues: (puzzle, VALID_SOLUTION),
    )
    client.get("/new")

    incorrect_board = [row[:] for row in VALID_SOLUTION]
    incorrect_board[0][0] = 4
    incorrect_response = client.post("/check", json={"board": incorrect_board})

    assert incorrect_response.status_code == 200
    assert incorrect_response.get_json() == {"incorrect": [[0, 0]]}
    assert sudoku_app.CURRENT["completed"] is False

    correct_response = client.post("/check", json={"board": VALID_SOLUTION})

    assert correct_response.status_code == 200
    assert correct_response.get_json() == {"incorrect": []}
    assert sudoku_app.CURRENT["completed"] is True
