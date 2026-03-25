# AI Coding Agent Instructions for COS-397 Chemistry Instrumentation

## Project Overview
**COS397_Black_ChemControl** - A chemistry lab instrument control system (Team Jack of All Spades capstone project). This system orchestrates communication between scientific instruments (Bruker IR spectrometer via Cary Bridge), a centralized server (Inter-Chem-Net API), a Tkinter-based UI, and data processing pipelines.

## Architecture

### Three-Controller Model
The system follows a clean three-controller pattern managed by `SystemController`:

1. **InstrumentController** (`components/InstrumentController.py`)
   - Communicates with Bruker Cary Bridge via Windows Registry (`HKEY_CURRENT_USER\Software\GenChem\CaryBridge`)
   - Methods: `setup()`, `take_sample()`, `take_blank()`, `ping()`
   - Returns `Sample` objects containing spectral data (wavelengths, intervals)
   - Registry keys: Queue, Params, State; poll interval 0.1s, timeout 60s

2. **ServerController** (`components/ServerController.py`)
   - REST API client for Inter-Chem-Net (ICN) staging environment
   - Requires `ICN_PRIVATE_API_KEY` in `.env` file
   - Methods: `ping()`, `login(username)`, `logout()`, `send_data()`, `send_all_data()`
   - API base: `https://interchemnet.avibe-stag.com/spectra/api/{endpoint}?key={api_key}`
   - Returns UUID tokens with expiry tracking

3. **SystemController** (`components/SystemController.py`)
   - Orchestrates workflow between controllers
   - Error code dictionary (0=success, 100=machine, 110=server, 220=account, 330=user, 400=no data, 550=no blank)
   - Workflow: `startUp()` → `signIn(username)` → `runLabMachine()`/`takeBlank()` → `signOut()`

### UI Layer
- **Framework**: Tkinter with ttk.Style themes ("clam" fallback)
- **Entry Point**: `components/User_Interface/main.py` → `PrototypeApp`
- **State Management**: `UIState` dataclass in `state.py` tracks: username, debug_mode, instrument_connected, server_status, blank_file_path, sample_files
- **Views**: SetupPageView, InstrumentPageView (frame-based routing in `PrototypeApp`)
- **Widgets**: Custom labeled_value, plot widgets; file dialogs for CSV import

### Data Model
**Sample class** (`components/Sample.py`):
- Attributes: name (str), type (str: "infrared"/"uv-vis"), data (float[]), interval (float)
- Represents single spectral measurement from instrument

## Key Workflows

### Startup Sequence
```
SystemController.startUp()
├─ InstrumentController.setup() → check Cary Bridge registry
└─ ServerController.connect() → verify ICN API
Returns: 0 (success) | 100 (machine fail) | 110 (server fail)
```

### Sample Analysis Workflow
```
SystemController.runLabMachine()
├─ InstrumentController.take_sample() → polls registry, returns Sample
├─ SystemController.send_data(data) → uploads to ICN
└─ Returns: (error_code, Sample) tuple
```

### Development Testing
- `test/test_basic_sort.py` - Sorting algorithm validation (uses pytest, numpy)
- `test/TestSystem.py`, `TestServer.py`, `TestInstrument.py`, `TestUI.py` - Component tests
- Run with: `pytest test/`

## Critical Conventions

### Import Patterns
- **Flexible imports**: InstrumentController uses try/except for relative vs absolute imports to support both test and installed module contexts
- Keep `components/Sample.py` importable from both contexts

### Environment Configuration
- `ServerController` loads `.env` for `ICN_PRIVATE_API_KEY` via `python-dotenv`
- No hardcoded API URLs or credentials

### Return Values
- All controller methods return error codes (int) or tuples (code, data)
- Convention: 0 = success; 100+ = specific error
- Check `SystemController.ErrorDictionary` when adding new error states

### Registry Interaction (Windows-Only)
- InstrumentController wraps `winreg` operations (CreateKey, SetValueEx, GetValue)
- Registry paths use `Software\GenChem\CaryBridge` as ROOT
- Always poll at 0.1s interval with 60s timeout for instrument operations

## Cross-Component Communication

| From | To | Method | Data |
|------|-----|--------|------|
| SystemController | InstrumentController | method calls | - |
| SystemController | ServerController | method calls | Sample data, user tokens |
| InstrumentController | SystemController | return Sample | Spectral data |
| ServerController | ICN API | HTTP GET/POST | JSON with UUID, credentials |
| UIState | Controllers | (separate binding) | User input, file paths |

## Testing Approach
- Tests are not integrated with controllers yet (TODO in codebase)
- Focus on unit tests for individual sorting/utility algorithms
- Future: mock ServerController API calls, mock registry for InstrumentController

## Dependencies
- `numpy`, `psutil`, `pytest` (requirements.txt)
- `requests` (ServerController API)
- `python-dotenv` (environment config)
- `tkinter` (standard library, UI)
- `brukeropus` (Bruker OPUS integration - see BrukerInstCon/)

## Common Tasks for Agents

**Adding a new endpoint**: Update ServerController method + SystemController workflow + error code
**Adding UI field**: Create widget in views/, update UIState dataclass, bind to controller method
**Adding instrument feature**: Extend InstrumentController method, create Sample variant, update SystemController logic
**Testing**: Write test in test/ directory using pytest fixtures, import from components/ with try/except pattern

## Files to Reference When Stuck
- [SystemController.py](SystemController.py) - system design & error codes
- [InstrumentController.py](InstrumentController.py) - registry patterns & Sample creation
- [ServerController.py](ServerController.py) - API integration patterns
- [app/app.py](components/User_Interface/app/app.py) - view routing & state binding
