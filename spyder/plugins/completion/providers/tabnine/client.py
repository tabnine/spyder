import logging
import json
import os
import platform
import subprocess
import stat
import threading
import zipfile

from qtpy.QtCore import QObject, QThread, Signal, QMutex
from spyder.plugins.completion.providers.tabnine import TABNINE_API_MAPPINGS
from spyder.plugins.completion.providers.kite.decorators import class_register
from urllib.request import urlopen, urlretrieve
from urllib.error import HTTPError

from spyder.plugins.completion.providers.tabnine.providers import (
    TabnineMethodProviderMixIn,
)

TABNINE_SERVER_URL = "https://update.tabnine.com/bundles"
TABNINE_EXECUTABLE = "TabNine"
VERSION = "0.0.1"

logger = logging.getLogger(__name__)


class TabnineDownloader(threading.Thread):
    def __init__(self, download_url, output_dir, tabnine):
        threading.Thread.__init__(self)
        self.download_url = download_url
        self.output_dir = output_dir
        self.tabnine = tabnine

    def run(self):
        try:
            if not os.path.isdir(self.output_dir):
                os.makedirs(self.output_dir)
            zip_path, _ = urlretrieve(self.download_url)
            with zipfile.ZipFile(zip_path, "r") as zf:
                for filename in zf.namelist():
                    zf.extract(filename, self.output_dir)
                    target = os.path.join(self.output_dir, filename)
                    add_execute_permission(target)
        except Exception as e:
            pass


@class_register
class TabnineClient(QObject, TabnineMethodProviderMixIn):

    sig_response_ready = Signal(int, dict)
    sig_client_started = Signal()
    sig_perform_request = Signal(int, str, object)

    def __init__(self):
        super().__init__()
        self._proc = None
        self._response = None
        self._install_dir = os.path.dirname(os.path.realpath(__file__))
        self._binary_dir = os.path.join(self._install_dir, "binaries")
        self._download_if_needed()

        self.sig_perform_request.connect(self.perform_request)
        self.mutex = QMutex()
        self.opened_files = {}

    def request(self, method, params):
        proc = self._get_running_tabnine()
        if proc is None or not method in TABNINE_API_MAPPINGS:
            return
        try:
            API_NAME = TABNINE_API_MAPPINGS[method]
            request_json = json.dumps(
                {"request": {API_NAME: params}, "version": "3.5.34"}
            )
            proc.stdin.write((request_json + "\n").encode("utf8"))
            proc.stdin.flush()
        except BrokenPipeError:
            self.restart()
            return None

        output = proc.stdout.readline().decode("utf8")
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return None

    def restart(self):
        if self._proc is not None:
            self._proc.terminate()
            self._proc = None
        path = get_tabnine_path(self._binary_dir)
        if path is None:
            return
        self._proc = subprocess.Popen(
            [
                path,
                "--client",
                "spyder",
                "--log-file-path",
                os.path.join(self._install_dir, "tabnine.log"),
                "--client-metadata",
                "pluginVersion={}".format(VERSION),
                "clientVersion={}".format(VERSION),  # TODO add real version
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        self.sig_client_started.emit()

    def _get_running_tabnine(self):
        if self._proc is None:
            self.restart()
        if self._proc is not None and self._proc.poll():
            self.restart()
        return self._proc

    def _download_if_needed(self):
        if os.path.isdir(self._binary_dir):
            tabnine_path = get_tabnine_path(self._binary_dir)
            if tabnine_path is not None:
                add_execute_permission(tabnine_path)
                return
        self._download()

    def _download(self):
        version = get_tabnine_version()
        distro = get_distribution_name()
        download_url = "{}/{}/{}/{}.zip".format(
            TABNINE_SERVER_URL, version, distro, TABNINE_EXECUTABLE
        )
        output_dir = os.path.join(self._binary_dir, version, distro)
        TabnineDownloader(download_url, output_dir, self).start()

    def perform_request(self, req_id, method, params):
        response = None
        if method in self.sender_registry:
            logger.debug("Perform request {0} with id {1}".format(method, req_id))
            handler_name = self.sender_registry[method]
            handler = getattr(self, handler_name)
            response = handler(params)
            if method in self.handler_registry:
                converter_name = self.handler_registry[method]
                converter = getattr(self, converter_name)
                if response is not None:
                    response = converter(params, response)
        if not isinstance(response, (dict, type(None))):
            if not running_under_pytest():
                self.sig_client_wrong_response.emit(method, response)
        else:
            self.sig_response_ready.emit(req_id, response or {})


def get_tabnine_version():
    version_url = "{}/{}".format(TABNINE_SERVER_URL, "version")

    try:
        return urlopen(version_url).read().decode("UTF-8").strip()
    except HTTPError:
        return None


ARCH_TRANSLATIONS = {
    "arm64": "aarch64",
    "AMD64": "x86_64",
}


def get_distribution_name():
    sysinfo = platform.uname()
    sys_architecture = sysinfo.machine

    if sys_architecture in ARCH_TRANSLATIONS:
        sys_architecture = arch_translations[sys_architecture]

    if sysinfo.system == "Windows":
        sys_platform = "pc-windows-gnu"

    elif sysinfo.system == "Darwin":
        sys_platform = "apple-darwin"

    elif sysinfo.system == "Linux":
        sys_platform = "unknown-linux-musl"

    elif sysinfo.system == "FreeBSD":
        sys_platform = "unknown-freebsd"

    else:
        raise RuntimeError(
            "Platform was not recognized as any of " "Windows, macOS, Linux, FreeBSD"
        )

    return "{}-{}".format(sys_architecture, sys_platform)


def get_tabnine_path(binary_dir):
    distro = get_distribution_name()
    versions = os.listdir(binary_dir)
    versions.sort(key=parse_semver, reverse=True)
    for version in versions:
        path = os.path.join(
            binary_dir, version, distro, executable_name(TABNINE_EXECUTABLE)
        )
        if os.path.isfile(path):
            return path


def parse_semver(s):
    try:
        return [int(x) for x in s.split(".")]
    except ValueError:
        return []


def add_execute_permission(path):
    st = os.stat(path)
    new_mode = st.st_mode | stat.S_IEXEC
    if new_mode != st.st_mode:
        os.chmod(path, new_mode)


def executable_name(name):
    if platform.system() == "Windows":
        return name + ".exe"
    else:
        return name
