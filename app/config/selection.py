# Selection filters for mutation runs.
# If left as None or empty list/tuple, *all* categories / mutations are included.

from typing import List, Optional

INCLUDE_CATEGORIES: Optional[List[str]] = [
    "VCR",
    "IPR",
    "IVR",
    "PDR",
    "PVCR",
]

# Variants (mutation_type) a serem incluídos
INCLUDE_MUTATION_TYPES: Optional[List[str]] = [
    "VCR_1_eq_to_tilde_gt",
    "IPR_ACT_DEL",
    "IVR_VAL_DEL",
    "PDR_CFG",
    "PVCR_VER_DEL",
] 