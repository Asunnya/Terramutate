import re

def apply_operators(content, mutations, only_idx: int | None = None):
    """Applies mutations to lines of *content*.

    Parameters
    ----------
    content : list[str]
        Lines of the file (read via ``readlines()``)
    mutations : list[dict]
        Each dict **must** have the keys ``pattern`` and ``replacement``.
    only_idx : int | None, optional
        If ``None`` (default) **all** occurrences of every pattern are replaced
        (legacy behaviour). When an integer is provided, *only* the global
        occurrence whose ordinal position equals ``only_idx`` is replaced and
        the remaining occurrences are kept intact. Occurrences are counted
        scanning the file top-down, left-to-right across **all** patterns.

    Returns
    -------
    list[str]
        The potentially mutated content.
    """

    # Single pass over the file content keeps cost linear.
    mutated_content: list[str] = []

    # Global counter that increases for every match found, regardless of which
    # pattern produced it. This guarantees determinism across multiple runs.
    occurrence_counter: int = 0

    for line in content:
        original_line = line  # keep reference for clarity; not strictly needed

        for mutation in mutations:
            pattern_raw = mutation["pattern"]
            # Ensure we don't match substrings inside larger numbers (e.g.,
            # ``count = 1`` inside ``count = 1000``). We append a *negative
            # look-ahead* that rejects a digit right after the pattern.
            pattern = rf"{pattern_raw}(?!\\d)"
            replacement = mutation["replacement"]

            if only_idx is None:
                # Legacy mode – replace all occurrences of *pattern* in *line*.
                line = re.sub(pattern, replacement, line)
            else:
                # Replace **at most** one occurrence if its global index matches
                # ``only_idx``. We rely on a closure to access and update the
                # outer scope variable ``occurrence_counter``.

                def _selective_repl(match):
                    nonlocal occurrence_counter
                    # increment first
                    current_idx = occurrence_counter
                    occurrence_counter += 1

                    if current_idx == only_idx:
                        return replacement
                    return match.group(0)

                line = re.sub(pattern, _selective_repl, line)

        mutated_content.append(line)

    return mutated_content
