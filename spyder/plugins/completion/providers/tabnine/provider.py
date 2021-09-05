# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""Kite completion HTTP client."""

# Standard library imports
import logging
import functools
import os
import os.path as osp

# Qt imports
from qtpy.QtCore import Slot
from qtpy.QtWidgets import QMessageBox

# Local imports
from spyder.api.config.decorators import on_conf_change
from spyder.config.base import _, running_under_pytest
from spyder.plugins.completion.api import SpyderCompletionProvider
from spyder.plugins.mainmenu.api import ApplicationMenus, ToolsMenuSections
from spyder.utils.icon_manager import ima
from spyder.utils.programs import run_program
from spyder.plugins.completion.providers.tabnine.tabnine_binary import TabnineBinary 


logger = logging.getLogger(__name__)


class TabnineProvider(SpyderCompletionProvider):
    COMPLETION_PROVIDER_NAME = 'tabnine'
    DEFAULT_ORDER = 1
    SLOW = True
    CONF_DEFAULTS = [
        ('spyder_runs', 1),
        ('show_installation_dialog', True),
        ('show_onboarding', True),
        ('show_installation_error_message', True),
        ('installers_available', True)
    ]
    CONF_VERSION = "0.1.0"

    def __init__(self, parent, config):
        super().__init__(parent, config)
        self._tabnine_binary = TabnineBinary()

    # ------------------ SpyderCompletionProvider methods ---------------------
    def get_name(self):
        return 'Tabnine'

    def send_request(self, language, req_type, req, req_id):
        logger.info(req)

