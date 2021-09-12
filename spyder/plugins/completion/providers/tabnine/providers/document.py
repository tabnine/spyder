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
from spyder.plugins.completion.providers.tabnine.decorators import send_request, handles
from spyder.plugins.completion.api import CompletionRequestTypes, CompletionItemKind

logger = logging.getLogger(__name__)

MAX_NUM_RESULTS = 5
TABNINE_ICON_SCALE = 416.14 / 526.8
TABNINE_COMPLETION = "Tabnine"


class DocumentProvider:
    @send_request(method=CompletionRequestTypes.DOCUMENT_DID_OPEN)
    def document_did_open(self, params):
        request = {}
        with QMutexLocker(self.mutex):
            self.opened_files[params["file"]] = params["text"]
        return request

    @send_request(method=CompletionRequestTypes.DOCUMENT_DID_CHANGE)
    def document_did_change(self, params):
        request = {}
        with QMutexLocker(self.mutex):
            self.opened_files[params["file"]] = params["text"]
        return request

    @send_request(method=CompletionRequestTypes.DOCUMENT_COMPLETION)
    def request_document_completions(self, params):
        filename = params["file"]
        before_offset = params["offset"]
        before = self.opened_files[filename][:before_offset]
        after = self.opened_files[filename][before_offset:]

        request = {
            "before": before,
            "after": after,
            "filename": filename,
            "max_num_results": MAX_NUM_RESULTS,
            "region_includes_beginning": True,
            "region_includes_end": True,
        }

        return request

    @handles(CompletionRequestTypes.DOCUMENT_COMPLETION)
    def convert_completion_request(self, request, response):
        spyder_completions = []

        before_offset = request["offset"]
        for i, completion in enumerate(response["results"]):
            entry = {
                "kind": CompletionItemKind.TABNINE,
                "label": completion["new_prefix"],
                "textEdit": {
                    "newText": completion["new_prefix"],
                    "range": {
                        "start": before_offset - len(response["old_prefix"]),
                        "end": before_offset,
                    },
                },
                "filterText": "",
                # Use the returned ordering
                "documentation": "Tabnine suggestion",
                "sortText": (i, 0),
                "provider": TABNINE_COMPLETION, 
                "icon": ("tabnine", TABNINE_ICON_SCALE),
            }

            spyder_completions.append(entry)

        return {"params": spyder_completions}
