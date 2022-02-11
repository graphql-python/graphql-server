# -*- coding: utf-8 -*-
"""
This holds all the implementation details of the MultipartDecoder
"""

# Code adapted from requests_toolbelt.multipart.decoder


from collections import defaultdict
from dataclasses import dataclass
import email.parser
from urllib.parse import unquote
from .error import HttpQueryError

def _split_on_find(content, bound):
    point = content.find(bound)
    return content[:point], content[point + len(bound):]


def _header_parser(string):

    headers = email.parser.HeaderParser().parsestr(string.decode('ascii')).items()
    return {
        k: v.encode('ascii')
        for k, v in headers
    }


class BodyPart(object):
    """
    The ``BodyPart`` object is a ``Response``-like interface to an individual
    subpart of a multipart response. It is expected that these will
    generally be created by objects of the ``MultipartDecoder`` class.
    Like ``Response``, there is a ``dict`` object named headers,
    ``content`` to access bytes, ``text`` to access unicode, and ``encoding``
    to access the unicode codec.
    """

    def __init__(self, content):
        headers = {}
        # Split into header section (if any) and the content
        if b'\r\n\r\n' in content:
            first, self.content = _split_on_find(content, b'\r\n\r\n')
            if first != b'':
                headers = _header_parser(first.lstrip())
        else:
            raise HttpQueryError(
                400,
                'Multipart content does not contain CR-LF-CR-LF'
            )
        self.headers = headers


class MultipartDecoder(object):
    """
    The ``MultipartDecoder`` object parses the multipart payload of
    a bytestring into a tuple of ``Response``-like ``BodyPart`` objects.
    The basic usage is::
        import requests
        from requests_toolbelt import MultipartDecoder
        response = requests.get(url)
        decoder = MultipartDecoder.from_response(response)
        for part in decoder.parts:
            print(part.headers['content-type'])
    If the multipart content is not from a response, basic usage is::
        from requests_toolbelt import MultipartDecoder
        decoder = MultipartDecoder(content, content_type)
        for part in decoder.parts:
            print(part.headers['content-type'])
    For both these usages, there is an optional ``encoding`` parameter. This is
    a string, which is the name of the unicode codec to use (default is
    ``'utf-8'``).
    """
    def __init__(self, content, content_type, encoding='utf-8'):
        #: Original Content-Type header
        self.content_type = content_type
        #: Response body encoding
        self.encoding = encoding
        #: Parsed parts of the multipart response body
        self.parts = tuple()
        self._find_boundary()
        self._parse_body(content)

    def _find_boundary(self):
        ct_info = tuple(x.strip() for x in self.content_type.split(';'))
        mimetype = ct_info[0]
        if mimetype.split('/')[0].lower() != 'multipart':
            raise HttpQueryError(
                400,
                "Unexpected mimetype in content-type: '{}'".format(mimetype)
            )
        for item in ct_info[1:]:
            attr, value = _split_on_find(
                item,
                '='
            )
            if attr.lower() == 'boundary':
                self.boundary = value.strip('"').encode('utf-8')

    @staticmethod
    def _fix_first_part(part, boundary_marker):
        bm_len = len(boundary_marker)
        if boundary_marker == part[:bm_len]:
            return part[bm_len:]
        else:
            return part

    def _parse_body(self, content):
        boundary = b''.join((b'--', self.boundary))

        def body_part(part):
            fixed = MultipartDecoder._fix_first_part(part, boundary)
            return BodyPart(fixed)

        def test_part(part):
            return (part != b'' and
                    part != b'\r\n' and
                    part[:4] != b'--\r\n' and
                    part != b'--')

        parts = content.split(b''.join((b'\r\n', boundary)))
        self.parts = tuple(body_part(x) for x in parts if test_part(x))


@dataclass
class File:
    content: bytes
    filename: str

def get_post_and_files(body, content_type):
    post = {}
    files = {}
    parts = MultipartDecoder(body, content_type).parts
    for part in parts:
        for name, header_value in part.headers.items():
            value, params = parse_header(header_value)
            if name.lower() == "content-disposition":
                filename = params.get("filename")
                if filename:
                    files[name.decode('utf-8')] = File(content=part.content, filename=filename)
                else:
                    name = params.get("name")
                    post[name.decode('utf-8')] = part.content.decode('utf-8')
    return post, files


def parse_header(line):
    """
    Parse the header into a key-value.
    Input (line): bytes, output: str for key/name, bytes for values which
    will be decoded later.
    """
    plist = _parse_header_params(b";" + line)
    key = plist.pop(0).lower().decode("ascii")
    pdict = {}
    for p in plist:
        i = p.find(b"=")
        if i >= 0:
            has_encoding = False
            name = p[:i].strip().lower().decode("ascii")
            if name.endswith("*"):
                # Lang/encoding embedded in the value (like "filename*=UTF-8''file.ext")
                # https://tools.ietf.org/html/rfc2231#section-4
                name = name[:-1]
                if p.count(b"'") == 2:
                    has_encoding = True
            value = p[i + 1 :].strip()
            if len(value) >= 2 and value[:1] == value[-1:] == b'"':
                value = value[1:-1]
                value = value.replace(b"\\\\", b"\\").replace(b'\\"', b'"')
            if has_encoding:
                encoding, lang, value = value.split(b"'")
                value = unquote(value.decode(), encoding=encoding.decode())
            pdict[name] = value
    return key, pdict


def _parse_header_params(s):
    plist = []
    while s[:1] == b";":
        s = s[1:]
        end = s.find(b";")
        while end > 0 and s.count(b'"', 0, end) % 2:
            end = s.find(b";", end + 1)
        if end < 0:
            end = len(s)
        f = s[:end]
        plist.append(f.strip())
        s = s[end:]
    return plist
