from .app import run_app


if __name__ == "__main__":
    try:
        run_app()
    except RuntimeError as exc:
        print(str(exc))
