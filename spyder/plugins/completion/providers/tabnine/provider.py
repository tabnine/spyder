import logging
import functools

# Local imports
from spyder.plugins.completion.api import (
    SpyderCompletionProvider,
    SERVER_CAPABILITES,
)
from spyder.plugins.mainmenu.api import ApplicationMenus, ToolsMenuSections
from spyder.utils.icon_manager import ima
from spyder.plugins.completion.providers.tabnine.client import TabnineClient

logger = logging.getLogger(__name__)

TRIGGER_CHARS = list(
    "abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz(=[%/{+#.,\\<+-|&*=$#@!"
)


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

    def __init__(self, parent, config):
        super().__init__(parent, config)
        self.client = TabnineClient()
        self.client.sig_client_started.connect(self.binary_client_ready)
        self.client.sig_response_ready.connect(
            functools.partial(
                self.sig_response_ready.emit, self.COMPLETION_PROVIDER_NAME
            )
        )

    def start_completion_services_for_language(self, language: str):
        self.register_completions_available(language)
        return True

    def get_name(self):
        return "Tabnine"

    def binary_client_ready(self):
        self.sig_provider_ready.emit(self.COMPLETION_PROVIDER_NAME)

    def start(self):
        logger.debug("Starting Tabnine")
        self.client.restart()

    def send_request(self, language, req_type, req, req_id):
        self.client.sig_perform_request.emit(req_id, req_type, req)

    def register_completions_available(self, language):
        server_capabilites = SERVER_CAPABILITES
        server_capabilites["completionProvider"]["triggerCharacters"] = TRIGGER_CHARS
        self.sig_language_completions_available.emit(
            server_capabilites,
            language,
        )
