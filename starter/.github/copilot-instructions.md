
# GitHub Copilot Instructions

## Project Overview
This project is a Flask-based Sudoku game refactoring project.
The goal is to transform the existing legacy Python application
into a modern, maintainable and feature-rich Sudoku game.

## Coding Standards
- Write clean, readable and maintainable code.
- Follow Python PEP 8 conventions.
- Use meaningful variable and function names.
- Prefer small, reusable functions.
- Avoid unnecessary code duplication.
- Add comments for complex business logic.
- Implement appropriate exception handling.

## Architecture
- Use Flask for backend development.
- Keep Sudoku logic separate from Flask routes.
- Use HTML, CSS and JavaScript for the frontend.
- Organize code into logical, reusable modules.
- Keep frontend and backend responsibilities separate.

## Sudoku Requirements
- Generate valid Sudoku puzzles.
- Ensure every generated puzzle has exactly one solution.
- Support Easy, Medium and Hard difficulties.
- Lock prefilled and hinted cells.
- Provide Hint and Check functionality.
- Display a completion message when solved.

## Frontend Requirements
- Create responsive desktop and mobile layouts.
- Support light and dark themes.
- Use alternating colors for 3x3 Sudoku blocks.
- Provide clear visual feedback for incorrect entries.
- Maintain accessible controls and readable typography.

## Testing Requirements
- Use pytest for automated testing.
- Preserve existing functionality during refactoring.
- Write tests for new features.
- Run tests after every significant change.
- Never modify application logic when asked only to
  establish the initial testing framework.

## Development Guidelines
- Inspect existing code before proposing changes.
- Explain significant architectural decisions.
- Avoid unnecessary dependencies.
- Never remove working functionality without justification.
- Follow the Udacity project rubric.
- Evaluate generated code before accepting changes.
