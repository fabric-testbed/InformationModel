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

import re
import json


class Tags:
    """
    A class representing a list of string tags that are no longer than a specified limit
    """
    TAG_PATTERN="^[\\w-]{1,255}$"
    compiled_pattern = re.compile(TAG_PATTERN)

    def __init__(self, *kwargs):
        """
        Provide tags as a list or individual parameters
        :param kwargs:
        """
        self.tags = list()
        for k in kwargs:
            if isinstance(k, list) or isinstance(k, tuple):
                for t in k:
                    Tags._check(t)
                    self.tags.append(t)
            else:
                Tags._check(k)
                self.tags.append(k)

    def to_json(self) -> str:
        """
        Convert list of tags to JSON
        :return:
        """
        return json.dumps(self.tags)

    def __str__(self) -> str:
        return str(self.tags)

    def __repr(self) -> str:
        return str(self)

    @classmethod
    def from_json(cls, json_string: str):
        """
        Create a Tags object from JSON string
        :return:
        """
        if json_string is None or len(json_string) == 0 or json_string == "None":
            return None

        d = json.loads(json_string)
        ret = cls(d)
        return ret

    @staticmethod
    def _check(tag: str):
        """
        Check that the tag conforms to our rules - it is a string of regular characters
        no longer than limit
        :param tag:
        :return:
        """
        if not isinstance(tag, str) or Tags.compiled_pattern.match(tag) is None:
            raise TagException(f'Tag {tag} does not match expected pattern {Tags.TAG_PATTERN}')

    def __iter__(self):
        return iter(list(self.tags))


class TagException(Exception):

    def __init__(self, msg):
        super().__init__(f'TagException: {msg}')
