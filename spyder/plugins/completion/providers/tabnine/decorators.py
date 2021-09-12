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
        response = self.request(method, params)
        return response

    wrapper._sends = method
    return wrapper

def handles(method_name):
    def wrapper(func):
        func._handle = method_name
        return func
    return wrapper
