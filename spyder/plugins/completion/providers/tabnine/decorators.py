import functools


def send_request(req=None, method=None):
    if req is None:
        return functools.partial(send_request, method=method)

    @functools.wraps(req)
    def wrapper(self, *args, **kwargs):
        url_params = {}
        params = req(self, *args, **kwargs)
        response = self.request(method, params)
        return response

    wrapper._sends = method
    return wrapper


def class_register(cls):
    cls.handler_registry = {}
    cls.sender_registry = {}
    for method_name in dir(cls):
        method = getattr(cls, method_name)
        if hasattr(method, "_handle"):
            cls.handler_registry.update({method._handle: method_name})
        if hasattr(method, "_sends"):
            cls.sender_registry.update({method._sends: method_name})
    return cls


def handles(method_name):
    def wrapper(func):
        func._handle = method_name
        return func

    return wrapper
