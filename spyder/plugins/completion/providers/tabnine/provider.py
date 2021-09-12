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
from spyder.plugins.completion.api import (
    SpyderCompletionProvider,
    CompletionItemKind,
    CompletionRequestTypes,
)
from spyder.plugins.mainmenu.api import ApplicationMenus, ToolsMenuSections
from spyder.utils.icon_manager import ima
from spyder.utils.programs import run_program
from spyder.plugins.completion.providers.tabnine.client import TabnineClient


logger = logging.getLogger(__name__)


class TabnineProvider(SpyderCompletionProvider):
    COMPLETION_PROVIDER_NAME = "tabnine"
    DEFAULT_ORDER = 1
    SLOW = True
    CONF_DEFAULTS = [
        ("spyder_runs", 1),
        ("show_installation_dialog", True),
        ("show_onboarding", True),
        ("show_installation_error_message", True),
        ("installers_available", True),
    ]
    CONF_VERSION = "0.1.0"
    MAX_NUM_RESULTS = 5

    def __init__(self, parent, config):
        super().__init__(parent, config)
        self.client = TabnineClient()
        self.client.sig_client_started.connect(self.binary_client_ready)
        self._file_contents = {}
        self.client.sig_response_ready.connect(
            functools.partial(self.sig_response_ready.emit,
                              self.COMPLETION_PROVIDER_NAME))

    def start_completion_services_for_language(self, language: str):
        return True

    def get_name(self):
        return "Tabnine"

    def binary_client_ready(self):
        self.sig_provider_ready.emit(self.COMPLETION_PROVIDER_NAME)

    def start(self):
        logger.error("Starting Tabnine")
        self.client.restart()

    def send_request(self, language, req_type, req, req_id):
        self.client.sig_perform_request.emit(req_id, req_type, req)
    
