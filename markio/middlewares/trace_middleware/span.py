from contextlib import asynccontextmanager

from starlette.types import Message, Scope

from .ctx import TraceCtx


class Span:
    """
    Complete HTTP lifecycle:
        request(before) --> request(after) --> response(before) --> response(after)
    """

    def __init__(self, scope: Scope):
        self.scope = scope

    async def request_before(self):
        """
        request_before: Handle header information, such as recording request body information
        """
        TraceCtx.set_id()

    async def request_after(self, message: Message):
        """
        request_after: Handle request bytes, such as recording request parameters
        """
        return message

    async def response(self, message: Message):
        """
        if message['type'] == "http.response.start":   -----> request-before
            pass
        if message['type'] == "http.response.body":    -----> request-after
            message.get('body', b'')
            pass
        """
        if message["type"] == "http.response.start":
            message["headers"].append((b"request-id", TraceCtx.get_id().encode()))
        return message


@asynccontextmanager
async def get_current_span(scope: Scope):
    yield Span(scope)
