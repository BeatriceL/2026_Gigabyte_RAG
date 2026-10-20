def main() -> None:
    import runpy
    import sys
    from pathlib import Path

    script = Path(__file__).resolve().with_name("generation.py")
    sys.path.insert(0, str(script.parent))
    runpy.run_path(str(script), run_name="__main__")
