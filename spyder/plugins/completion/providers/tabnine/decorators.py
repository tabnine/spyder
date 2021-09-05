# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""Kite client dispatcher decorators."""

import functools


def send_request(req=None, method=None):
    """Call function req and then send its results via HTTP."""
    if req is None:
        return functools.partial(send_request, method=method)

    @functools.wraps(req)
    def wrapper(self, *args, **kwargs):
        url_params = {}
        params = req(self, *args, **kwargs)
        if isinstance(params, tuple):
            params, url_params = params
        response = self.send(method, params, url_params)
        return response
    wrapper._sends = method
    return wrapper
