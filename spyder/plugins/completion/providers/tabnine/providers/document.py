# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""Kite document requests handlers and senders."""

from collections import defaultdict
import logging
import hashlib

import os
import os.path as osp

from qtpy.QtCore import QMutexLocker
from spyder.plugins.completion.providers.tabnine.decorators import (
    send_request, handles)
from spyder.plugins.completion.api import (
    CompletionRequestTypes, CompletionItemKind)

logger = logging.getLogger(__name__)

class DocumentProvider:

    @send_request(method=CompletionRequestTypes.DOCUMENT_COMPLETION)
    def request_document_completions(self, params):
        text = self.opened_files[params['file']]
        request = {
            'filename': osp.realpath(params['file']),
            'editor': 'spyder',
            'no_snippets': not self.enable_code_snippets,
            'text': text,
            'position': {
                'begin': params['selection_start'],
                'end': params['selection_end'],
            },
            'offset_encoding': 'utf-16',
        }
        return request
