"""Desktop Cat : un chat en pixel art qui vit sur ton bureau Windows."""

__version__ = "0.3.0"

import logging as _logging

_logging.getLogger("desktopcat").addHandler(_logging.NullHandler())   # sans journal actif : silence, pas de sortie parasite
