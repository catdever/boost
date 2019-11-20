from requests.structures import CaseInsensitiveDict as CID
from urllib.parse import urlparse, parse_qsl, urlunparse, urlencode
from http.client import responses
from typing import Dict

HTTP1_1 = 'HTTP/1.1'


class StatusRequest(Exception):
    pass


class UnknownRequest(Exception):
    pass


class MissingQuery(Exception):
    pass


class URL:
    """Parsed URL: scheme://netloc/path;params?query#fragment"""

    def __init__(self, url: bytes):
        url = urlparse(url.decode())
        self.scheme = url.scheme  # type: str
        self.netloc = url.netloc  # type: str
        self.path = url.path  # type: str
        self.params = url.params  # type: str
        self.query = dict(parse_qsl(url.query)) if url.query else {}  # type: Dict[str, str]
        self.fragment = url.fragment  # type: str

    def __repr__(self):
        return urlunparse((self.scheme, self.netloc, self.path, self.params,
                           urlencode(self.params), self.fragment))


class Request:
    """The object that the server must pack all requests into. This is
    necessary to support multiple search apis."""
    __slots__ = ['method', 'url', 'params', 'version', 'headers', 'body',
                 'topk']

    def __init__(self):
        self.version = HTTP1_1
        self.headers = CID()
        self.url = None  # type: URL
        self.body = bytes()
        self.method = str()
        self.params = dict()

    def __repr__(self):
        return '<Request %s %s>' % (self.url, self.method)

    def prepare(self) -> bytes:
        self.headers['content-length'] = str(len(self.body))
        headers = ''.join(
            '\r\n%s: %s' % (k, v) for k, v in self.headers.items())
        return '{method} {url} {version}{headers}\r\n\r\n'.format(
            method=self.method, url=str(self.url), version=self.version,
            headers=headers
        ).encode() + self.body


class Response:
    """The object that each response must be packed into before sending. Same
    reason as the Request object. """
    __slots__ = ['version', 'status', 'headers', 'body']

    def __init__(self):
        self.version = HTTP1_1
        self.status = 200
        self.headers = CID()
        self.body = bytes()

    def __repr__(self):
        return '<Response %s %s>' % (self.status, self.reason)

    @property
    def reason(self):
        return responses[self.status]

    def prepare(self) -> bytes:
        self.headers['content-length'] = str(len(self.body))
        return '{version} {status} {reason}{headers}\r\n\r\n'.format(
            version=self.version, status=self.status, reason=self.reason,
            headers=''.join(
                '\r\n%s: %s' % (k, v) for k, v in self.headers.items())
        ).encode() + self.body
