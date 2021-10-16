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

import json


class MeasurementData:
    """
    Measurement data attaches as a property on any node and is an opaque JSON blob
    """
    def __init__(self, data: str or None):
        """
        data has to be a valid JSON string
        :param data:
        """
        try:
            if data is not None and len(data) > 0:
                if len(data) > 1024*1024:
                    raise MeasurementDataError(f'MeasurementData JSON string is too long ({len(data)} > 1024*1024')
                json.loads(data)
                self._data = data
            else:
                self._data = "{}"
        except json.JSONDecodeError:
            raise MeasurementDataError(f'Unable to decode measurement data {data} as valid JSON ')

    @property
    def data(self):
        return self._data

    def __str__(self):
        return self._data or ""

    def __repr(self):
        return str(self)


class MeasurementDataError(Exception):

    def __init__(self, msg):
        super().__init__(f'MeasurementDataError: invalid measurement data due to {msg}')