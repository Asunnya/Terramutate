"""Entry-point de conveniência.

Permite executar a ferramenta simplesmente com:

    python main.py <args>

que delega ao verdadeiro CLI localizado em ``app/main.py``.
"""

from app.main import main as _app_main  


def main(): 
    _app_main()


if __name__ == "__main__":
    main()
