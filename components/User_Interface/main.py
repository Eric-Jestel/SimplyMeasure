from pathlib import Path
import sys


def main():
    PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

    from app.app import App
    app = App(PROJECT_ROOT)
    app.run()


if __name__ == "__main__":
    main()
