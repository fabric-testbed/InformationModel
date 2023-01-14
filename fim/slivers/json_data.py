#!/usr/bin/env python3
# MIT License
#
# Copyright (c) 2020 FABRIC Testbed
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
# Author: Ilya Baldin (ibaldin@renci.org)
from abc import ABC, abstractmethod
from typing import Any

import json


class JSONDataError(Exception):

    def __init__(self, msg):
        super().__init__(f'JSONDataError: invalid JSON data due to {msg}')


class MeasurementDataError(JSONDataError):

    def __init__(self, msg):
        super().__init__(f'MeasurementDataError: invalid user data due to {msg}')


class UserDataError(JSONDataError):

    def __init__(self, msg):
        super().__init__(f'UserDataError: invalid user data due to {msg}')


class LayoutDataError(JSONDataError):

    def __init__(self, msg):
        super().__init__(f'LayoutDataError: invalid layout data due to {msg}')


class JSONData(ABC):
    """
    Base class for any JSON-formatted blob of data stored as a property. Any child
    must define MAX_SIZE.
    """

    @abstractmethod
    def __init__(self, data: Any or None, excep):
        """
        data has to be a valid JSON string or a Python object
        :param data:
        :param excep: default excaption object
        """

        if data is not None and isinstance(data, str):
            if len(data) > self.MAX_SIZE:
                raise excep(f'Data JSON string is too long ({len(data)} > {self.MAX_SIZE}B')
            try:
                json.loads(data)
            except json.JSONDecodeError:
                raise excep(f'Unable to decode data {data} as valid JSON ')
            self._data = data
        elif data is not None:
            try:
                self._data = json.dumps(data)
                if len(self._data) > self.MAX_SIZE:
                    raise excep(f'Data object is too large: '
                                               f'{len(self._data)} > {self.MAX_SIZE}B')
            except TypeError:
                raise excep(f'Unable to encode data as valid JSON')
        else:
            self._data = "{}"

    @property
    def data(self):
        """
        Return as object
        """
        if self._data is not None:
            return json.loads(self._data)
        return self._data

    @property
    def json(self):
        """
        Return as JSON
        """
        return self._data

    def __str__(self):
        return str(self._data)

    def __repr(self):
        return str(self)


class MeasurementData(JSONData):

    MAX_SIZE = 4096

    def __init__(self, data: Any or None):
        super().__init__(data, MeasurementDataError)


class UserData(JSONData):

    MAX_SIZE = 2048

    def __init__(self, data: Any or None):
        super().__init__(data, UserDataError)


class LayoutData(JSONData):

    MAX_SIZE = 1024

    def __init__(self, data: Any or None):
        super().__init__(data, LayoutDataError)