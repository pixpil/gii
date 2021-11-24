"""
Contains a linter mode which validates the current json text in the editor.
"""
import json
import re
from pyqode.core.modes import CheckerMode, CheckerMessages


_MATCH = re.compile('^.*: line \d+ column \d+')
_LINE = re.compile('line \d+')
_COLUMN = re.compile('column \d+')


def json_linter(data):
    """
    Worker function that checks a json string.

    :param data: request data
    """
    code = data['code']
    try:
        json.loads(code)
    except ValueError as e:
        msg, line, column = str(e), -1, -1
        match = _MATCH.match(msg)
        if match:
            line = int(_LINE.findall(msg)[0].replace('line ', '')) - 1
            column = int(_COLUMN.findall(msg)[0].replace('column ', ''))
            msg = _MATCH.match(msg).group(0).split(':')[0].replace(':', '')
        return [(msg, CheckerMessages.ERROR, line, column)]
    else:
        return []


class JSONLinter(CheckerMode):
    """
    Provides a JSON Linter mode.
    """
    def __init__(self):
        super(JSONLinter, self).__init__(json_linter)
