#!/usr/bin/python3

from sensible_config import VENV_SITE_PACKAGES_DIR

import site
site.addsitedir(VENV_SITE_PACKAGES_DIR)

from flipflop import WSGIServer
from werkzeug.contrib.fixers import CGIRootFix
from app import app

if __name__ == '__main__':
    WSGIServer(app).run()

