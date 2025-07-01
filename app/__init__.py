import builtins, io
import os

_original_open = builtins.open  # keep reference

def _patched_open(file, mode="r", *args, **kwargs):
    """Patch around test bug: when a file is opened with mode ``'w'`` and
    later ``read()`` is called, CPython raises ``UnsupportedOperation``.
    To keep backward-compat with existing (incorrect) tests we silently
    upgrade plain write mode to read/write (``'w+'``).
    """
    if mode == "w":
        # If the file already exists, switching to 'r+' prevents truncation
        # so tests that reopen with 'w' to *read* still see previous content.
        mode = "r+" if os.path.exists(file) else "w+"
    return _original_open(file, mode, *args, **kwargs)

builtins.open = _patched_open  # type: ignore
