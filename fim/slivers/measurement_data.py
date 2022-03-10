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
from abc import ABC
from typing import Any

import json


class MeasurementData:
    """
    Measurement data attaches as a property on any graph node and is represented as an opaque JSON blob
    """
    MF_SIZE = 10240

    def __init__(self, data: Any or None):
        """
        data has to be a valid JSON string
        :param data:
        """

        if data is not None and isinstance(data, str):
            if len(data) > self.MF_SIZE:
                raise MeasurementDataError(f'MeasurementData JSON string is too long ({len(data)} > {self.MF_SIZE}B')
            try:
                json.loads(data)
            except json.JSONDecodeError:
                raise MeasurementDataError(f'Unable to decode measurement data {data} as valid JSON ')
            self._data = data
        elif data is not None:
            try:
                self._data = json.dumps(data)
                if len(self._data) > 1024*1024:
                    raise MeasurementDataError(f'MeasurementData object is too large: '
                                               f'{len(self._data)} > {self.MF_SIZE}B')
            except TypeError:
                raise MeasurementDataError(f'Unable to encode data as valid JSON')
        else:
            self._data = "{}"

    @property
    def data(self):
        if self._data is not None:
            return json.loads(self._data)
        return self._data

    def __str__(self):
        return str(self._data)

    def __repr(self):
        return str(self)


class MeasurementDataError(Exception):

    def __init__(self, msg):
        super().__init__(f'MeasurementDataError: invalid measurement data due to {msg}')