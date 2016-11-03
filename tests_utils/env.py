'''
    env.py : this module appends the root directory to sys.path
    in order to allow keeping all test/utilities in this subdir
    to prevent rootdir cluttering.
'''

import sys
import os

# append module root directory to sys.path
sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)
