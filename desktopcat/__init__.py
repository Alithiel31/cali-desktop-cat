"""Desktop Cat : un chat en pixel art qui vit sur ton bureau Windows."""

__version__ = "0.5.0"

import logging as _logging

# sans journal actif : silence, pas de sortie parasite
_logging.getLogger("desktopcat").addHandler(_logging.NullHandler())
