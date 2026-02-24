from contextlib import asynccontextmanager

from starlette.datastructures import MutableHeaders
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
        incoming_request_id = ""
        for key, value in self.scope.get("headers", []):
            if key in {b"x-request-id", b"request-id"}:
                incoming_request_id = value.decode("utf-8", errors="ignore").strip()
                if incoming_request_id:
                    break
        TraceCtx.set_id(incoming_request_id)

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
            headers = MutableHeaders(raw=message["headers"])
            request_id = TraceCtx.get_id().encode()
            if "x-request-id" not in headers:
                headers.append("X-Request-ID", request_id.decode())
            if "request-id" not in headers:
                headers.append("request-id", request_id.decode())
        return message


@asynccontextmanager
async def get_current_span(scope: Scope):
    yield Span(scope)
