# Project: Radio Shell (Python)

Terminal-based FM radio player specializing in Turkish and global radio stations.

## Architectural Overview

The project is structured as a layered CLI application:

1.  **Entry Point (`src/radio/main.py`):** Orchestrates service initialization and starts the interactive shell.
2.  **Shell Layer (`src/radio/shell.py`, `commands_*.py`):** Uses `prompt_toolkit` for the interactive REPL. Commands are modularized:
    *   `commands_basic.py`: Listing and searching.
    *   `commands_playback.py`: Playback control (volume, play/stop).
    *   `commands_management.py`: CRUD for stations, favorites, and themes.
3.  **Service Layer (`src/radio/services/`):** Pure logic for data management and external APIs.
    *   `StationService`: Manages `stations.json` and user custom stations.
    *   `RadioBrowserService`: Integrates with radio-browser.info API.
4.  **Player Layer (`src/radio/player.py`):** Manages `ffplay` (ffmpeg) subprocesses for audio streaming.
5.  **UI Layer (`src/radio/ui.py`):** Centralizes `rich` console formatting and themes.

## Tech Stack

*   **Language:** Python 3.10+ (Current: 3.14)
*   **Shell:** `prompt_toolkit`
*   **UI:** `rich`
*   **Audio Engine:** `ffplay` (external dependency)
*   **Testing:** `pytest`

## Development Workflows

### Setup & Run
*   Execute `./radio.sh` to start the application. It handles venv and dependencies automatically.
*   Manual start: `export PYTHONPATH=. && python3 -m src.radio.main`

### Testing
*   Run tests using `pytest`: `pytest tests/`
*   Ensure all new services or logic have corresponding tests in the `tests/` directory.

## Coding Conventions & Style

*   **Naming:** Follow PEP 8 (snake_case for functions/variables, PascalCase for classes).
*   **UI/UX:** Always use the `src/radio/ui.py` utility for terminal output to maintain consistent themes and styling. Do not use raw `print()` statements.
*   **Error Handling:** Catch and display user-friendly messages via `ui.print_error()`.
*   **Internationalization:** Primary support is for Turkish. Ensure UTF-8 compatibility for Turkish characters.
*   **Dependency Management:** Add new dependencies to `requirements.txt`.

## Persistence

User data is stored in `~/.radio-shell/`:
*   `favorites.json`: List of favorite station IDs.
*   `custom-stations.json`: User-defined radio stations.
*   `settings.json`: Volume, last station, etc.
*   `recordings/`: Directory for MP3 captures.

## Legacy Context
This project was previously a Java Spring Shell application. Some artifacts like `target/`, `pom.xml`, or `org/` directory might still exist but the Python implementation in `src/radio/` is the current source of truth.
