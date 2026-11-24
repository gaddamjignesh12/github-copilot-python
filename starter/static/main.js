// Client-side rendering and interaction for the Flask-backed Sudoku
const SIZE = 9;
const LEADERBOARD_STORAGE_KEY = 'sudokuLeaderboard';
const THEME_STORAGE_KEY = 'sudokuTheme';
const MAX_LEADERBOARD_ENTRIES = 10;
let puzzle = [];
let hintsUsed = 0;
let timerInterval = null;
let gameStartedAt = null;
let gameCompleted = false;
let gameDifficulty = 'medium';
let completionTimeSeconds = null;
let scoreSubmitted = false;

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  const toggle = document.getElementById('theme-toggle');
  const darkTheme = theme === 'dark';
  toggle.innerText = `Switch to ${darkTheme ? 'light' : 'dark'} mode`;
  toggle.setAttribute('aria-pressed', String(darkTheme));
}

function initializeTheme() {
  let savedTheme = null;
  try {
    savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
  } catch (error) {
    showMessage('Unable to read the saved theme preference.', 'var(--error)');
  }

  const systemPrefersDark = window.matchMedia
    && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const theme = savedTheme === 'light' || savedTheme === 'dark'
    ? savedTheme
    : (systemPrefersDark ? 'dark' : 'light');
  applyTheme(theme);

  document.getElementById('theme-toggle').addEventListener('click', () => {
    const nextTheme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    applyTheme(nextTheme);
    try {
      localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
    } catch (error) {
      showMessage('Theme changed, but could not be saved in this browser.', 'var(--error)');
    }
  });
}

function showMessage(message, color = 'var(--text)') {
  const msg = document.getElementById('message');
  msg.innerText = message;
  msg.style.color = color;
}

function normalizePlayerName(value) {
  const name = value.trim();
  if (!name || name.length > 40 || /[\u0000-\u001f\u007f]/.test(name)) {
    return null;
  }
  return name;
}

function isLeaderboardEntry(entry) {
  return entry
    && typeof entry.name === 'string'
    && normalizePlayerName(entry.name) === entry.name
    && Number.isInteger(entry.timeSeconds)
    && entry.timeSeconds >= 0
    && ['easy', 'medium', 'hard'].includes(entry.difficulty)
    && Number.isInteger(entry.hintsUsed)
    && entry.hintsUsed >= 0;
}

function readLeaderboard() {
  try {
    const saved = localStorage.getItem(LEADERBOARD_STORAGE_KEY);
    if (saved === null) return [];

    const entries = JSON.parse(saved);
    if (!Array.isArray(entries)) {
      throw new TypeError('Saved leaderboard data is not a list.');
    }
    return entries.filter(isLeaderboardEntry);
  } catch (error) {
    showMessage('Unable to read the saved leaderboard.', 'var(--error)');
    return null;
  }
}

function sortedTopScores(entries) {
  return entries
    .slice()
    .sort((first, second) => first.timeSeconds - second.timeSeconds)
    .slice(0, MAX_LEADERBOARD_ENTRIES);
}

function formatTime(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, '0');
  const seconds = (totalSeconds % 60).toString().padStart(2, '0');
  return `${minutes}:${seconds}`;
}

function renderLeaderboard(entries = null) {
  const scores = sortedTopScores(entries === null ? (readLeaderboard() || []) : entries);
  const list = document.getElementById('leaderboard-list');
  const emptyMessage = document.getElementById('leaderboard-empty');
  list.innerHTML = '';
  emptyMessage.hidden = scores.length > 0;

  for (const score of scores) {
    const item = document.createElement('li');
    const name = document.createElement('span');
    name.className = 'leaderboard-name';
    name.textContent = score.name;
    const details = document.createElement('span');
    details.textContent =
      `${formatTime(score.timeSeconds)} · ${score.difficulty} · ${score.hintsUsed} hints`;
    item.append(name, details);
    list.appendChild(item);
  }
}

function openScoreDialog() {
  const dialog = document.getElementById('score-dialog');
  document.getElementById('player-name').value = '';
  document.getElementById('player-name-error').innerText = '';
  dialog.showModal();
  document.getElementById('player-name').focus();
}

function saveCompletedGame(event) {
  event.preventDefault();
  if (!gameCompleted || scoreSubmitted || completionTimeSeconds === null) return;

  const input = document.getElementById('player-name');
  const name = normalizePlayerName(input.value);
  const nameError = document.getElementById('player-name-error');
  if (name === null) {
    nameError.innerText = 'Enter a name of 1 to 40 characters.';
    input.focus();
    return;
  }

  const scores = readLeaderboard();
  if (scores === null) return;
  const newScore = {
    name,
    timeSeconds: completionTimeSeconds,
    difficulty: gameDifficulty,
    hintsUsed,
  };
  const updatedScores = sortedTopScores([
    ...scores,
    newScore,
  ]);
  try {
    localStorage.setItem(LEADERBOARD_STORAGE_KEY, JSON.stringify(updatedScores));
  } catch (error) {
    showMessage('Unable to save the leaderboard in this browser.', 'var(--error)');
    return;
  }

  scoreSubmitted = true;
  renderLeaderboard(updatedScores);
  document.getElementById('score-dialog').close();
  if (updatedScores.includes(newScore)) {
    showMessage('Your time was added to the leaderboard!', 'var(--success)');
  } else {
    showMessage('Your time did not make the Top 10.');
  }
}

function createBoardElement() {
  const boardDiv = document.getElementById('sudoku-board');
  boardDiv.innerHTML = '';
  for (let i = 0; i < SIZE; i++) {
    const rowDiv = document.createElement('div');
    rowDiv.className = 'sudoku-row';
    for (let j = 0; j < SIZE; j++) {
      const input = document.createElement('input');
      input.type = 'text';
      input.maxLength = 1;
      input.className = 'sudoku-cell';
      input.dataset.row = i;
      input.dataset.col = j;
      input.addEventListener('input', (e) => {
        const val = e.target.value.replace(/[^1-9]/g, '');
        e.target.value = val;
        e.target.classList.remove('incorrect');
        if (isBoardFilled()) {
          checkSolution(false);
        }
      });
      rowDiv.appendChild(input);
    }
    boardDiv.appendChild(rowDiv);
  }
}

function renderPuzzle(puz) {
  puzzle = puz;
  createBoardElement();
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  for (let i = 0; i < SIZE; i++) {
    for (let j = 0; j < SIZE; j++) {
      const idx = i * SIZE + j;
      const val = puzzle[i][j];
      const inp = inputs[idx];
      if (val !== 0) {
        inp.value = val;
        inp.disabled = true;
        inp.classList.add('prefilled');
      } else {
        inp.value = '';
        inp.disabled = false;
      }
    }
  }
}

function getBoard() {
  const inputs = document.getElementById('sudoku-board').getElementsByTagName('input');
  const board = [];
  for (let i = 0; i < SIZE; i++) {
    board[i] = [];
    for (let j = 0; j < SIZE; j++) {
      const value = inputs[i * SIZE + j].value;
      board[i][j] = value ? parseInt(value, 10) : 0;
    }
  }
  return board;
}

function isBoardFilled() {
  const inputs = document.getElementById('sudoku-board').getElementsByTagName('input');
  return Array.from(inputs).every(input => input.value !== '');
}

function setTimerRunning(running) {
  if (timerInterval !== null) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
  if (!running || gameStartedAt === null) return;

  const updateTimer = () => {
    const elapsed = Math.floor((Date.now() - gameStartedAt) / 1000);
    const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
    const seconds = (elapsed % 60).toString().padStart(2, '0');
    document.getElementById('timer').innerText = `${minutes}:${seconds}`;
  };
  updateTimer();
  timerInterval = setInterval(updateTimer, 1000);
}

async function newGame() {
  const difficulty = document.getElementById('difficulty').value;
  const res = await fetch(`/new?difficulty=${encodeURIComponent(difficulty)}`);
  const data = await res.json();
  if (!res.ok) {
    showMessage(data.error || 'Unable to start a new game.', 'var(--error)');
    return;
  }
  gameCompleted = false;
  scoreSubmitted = false;
  completionTimeSeconds = null;
  gameDifficulty = difficulty;
  hintsUsed = 0;
  renderPuzzle(data.puzzle);
  showMessage('');
  document.getElementById('hints-used').innerText = hintsUsed;
  gameStartedAt = Date.now();
  setTimerRunning(true);
}

async function checkSolution(showFeedback = true) {
  if (gameCompleted) return;
  const inputs = document.getElementById('sudoku-board').getElementsByTagName('input');
  const res = await fetch('/check', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({board: getBoard()})
  });
  const data = await res.json();
  if (gameCompleted) return;
  const msg = document.getElementById('message');
  if (data.error) {
    msg.style.color = 'var(--error)';
    msg.innerText = data.error;
    return;
  }

  const incorrect = new Set(data.incorrect.map(cell => cell[0] * SIZE + cell[1]));
  let incorrectEntries = 0;
  for (let idx = 0; idx < inputs.length; idx++) {
    const input = inputs[idx];
    if (input.disabled) continue;
    input.classList.toggle('incorrect', incorrect.has(idx) && input.value !== '');
    if (incorrect.has(idx) && input.value !== '') {
      incorrectEntries++;
    }
  }

  if (data.incorrect.length === 0) {
    gameCompleted = true;
    for (const input of inputs) input.disabled = true;
    setTimerRunning(false);
    completionTimeSeconds = Math.floor((Date.now() - gameStartedAt) / 1000);
    showMessage('Congratulations! You solved it!', 'var(--success)');
    openScoreDialog();
  } else if (showFeedback && incorrectEntries > 0) {
    msg.style.color = 'var(--error)';
    msg.innerText = 'Some cells are incorrect.';
  } else if (showFeedback) {
    msg.style.color = 'var(--text)';
    msg.innerText = 'No incorrect entries. Keep going!';
  }
}

async function getHint() {
  if (gameCompleted) return;
  const msg = document.getElementById('message');
  const res = await fetch('/hint', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({board: getBoard()})
  });
  const data = await res.json();
  if (!res.ok) {
    msg.style.color = 'var(--error)';
    msg.innerText = data.error || 'Unable to get a hint.';
    return;
  }

  const input = document.querySelector(
    `.sudoku-cell[data-row="${data.row}"][data-col="${data.col}"]`
  );
  input.value = data.value;
  input.disabled = data.locked;
  input.classList.remove('incorrect');
  input.classList.add('hinted');
  hintsUsed = data.hints_used;
  document.getElementById('hints-used').innerText = hintsUsed;
  msg.style.color = 'var(--info)';
  msg.innerText = 'Hint revealed and locked.';
  if (isBoardFilled()) {
    checkSolution(false);
  }
}

// Wire buttons
window.addEventListener('load', () => {
  initializeTheme();
  document.getElementById('new-game').addEventListener('click', newGame);
  document.getElementById('check-solution').addEventListener('click', checkSolution);
  document.getElementById('hint').addEventListener('click', getHint);
  document.getElementById('score-form').addEventListener('submit', saveCompletedGame);
  document.getElementById('score-dialog').addEventListener('cancel', event => {
    event.preventDefault();
  });
  renderLeaderboard();
  // initialize
  newGame();
});