# THE FORGE  |  Copyright (c) 2026 Yannie D. Forest. All rights reserved.
# NO LICENCE IS GRANTED. See LICENCE.txt.
#
# PyInstaller runtime hook (named in the_forge.spec): a windowed program has
# no console, so Python gives it no standard output. Anything printed goes
# nowhere instead of stopping the program. The same hook as Inkwell's
# (Inkwell-Windows/build/quiet_console.py). You do not run this file yourself.
import os
import sys

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")
