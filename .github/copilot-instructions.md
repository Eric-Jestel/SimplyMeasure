# AI Coding Agent Instructions for COS-397 Chemistry Instrumentation

## Big Picture (current code)
- Main orchestration lives in `components/SystemController.py`; UI calls this controller directly.
- UI is **PyQt6**, not Tkinter. Entry is `components/User_Interface/main.py`, app shell is `components/User_Interface/app/app.py` (`QMainWindow` + `QStackedWidget`).
- Instrument side is registry/mailbox based in `components/InstrumentController.py` (Windows-only `winreg`, ADL launcher).
- Server side is REST + local file staging in `components/ServerController.py`.

## Controller Contracts You Must Preserve
- `SystemController` returns numeric error codes (`0`, `100`, `110`, `220`, `300`, `330`, `400`, `550`) and tuples for data-bearing operations.
- `InstrumentController.take_sample(filename)` currently returns a **result file path string** (not `Sample`).
- `InstrumentController.take_blank(filename)` returns `bool`; blank path is kept in `InstrumentController.blank_file`.
- `ServerController.send_data(samplePath)` expects a staged file path named like `username_datetime_unsent.json`.

## Logging Convention (project-specific)
- Controllers now use explicit print tracing:
   - `[...][RECEIVED]` when a command enters a method
   - `[...][TX]` when data is sent externally (registry/API)
   - `[...][EXECUTED]` when method completes with result
- Keep this pattern when adding/modifying controller methods.

## Data Flow
- Typical run path in `SystemController.runLabMachine()`:
   1. `InstrumentController.take_sample(targetFilename)`
   2. `ServerController.process_sample(csv_path)` (currently referenced by `SystemController`)
   3. `ServerController.send_all_data()` to upload staged unsent JSON files
- Blank flow:
   - `takeBlank(filename)` → `InstrumentController.take_blank(filename)`
   - `setBlank(path)` → `InstrumentController.set_blank(path)`

## UI Wiring (important files)
- Setup screen: `components/User_Interface/app/views/setup_page.py`
   - Connect/reconnect instrument/server, blank capture/load/reset, debug mode toggle.
- Session screen: `components/User_Interface/app/views/instrument_page.py`
   - Username login (`SystemController.signIn`) and sample capture (`SystemController.runLabMachine`).
- Shared state: `components/User_Interface/app/state.py` (`username`, `debug_mode`, `instrument_connected`, `server_status`, `blank_file_path`, `sample_files`).

## Dev Workflows
- Run UI: `python components/User_Interface/main.py`
- Tests: `pytest test/`
- Existing tests are strongest around instrument mailbox helpers (`test/TestInstrument.py`) and sorting utilities (`test/test_basic_sort.py`).

## Known Gaps / Incomplete Areas (do not assume finished)
- `SystemController` references `ServerController.process_sample(...)`; ensure this method exists/works before refactors.
- `SystemController.takeSample()` still calls `take_sample()` without filename (signature mismatch risk).
- `SystemControllerSample` is legacy/demo code and can diverge from production behavior.

## Integration Rules
- Keep `ICN_PRIVATE_API_KEY` loaded from `.env` in `ServerController`.
- Do not hardcode secrets or endpoint keys.
- Keep Windows registry constants and mailbox timing behavior in `InstrumentController` unless explicitly changing protocol.
