# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
Astromatic-Wrapper
==================

This Package is a wrapper for E. Bertin's AstrOmatic Software suite
"""

# Affiliated packages may add whatever they like to this file, but
# should keep this content at the top.
# ----------------------------------------------------------------------------
from ._astropy_init import *
# ----------------------------------------------------------------------------

# For egg_info test builds to pass, put package imports here.
if not _ASTROPY_SETUP_:
    from example_mod import *

import astromatic_wrapper.api
import astromatic_wrapper.utils