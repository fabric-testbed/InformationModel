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
"""
Abstract definition of ADM (Aggregate Delegation Model) functionality
"""

from abc import ABCMeta, abstractmethod


class ABCADMMixin(metaclass=ABCMeta):
    """
    Interface for an ADM Mixin on top of a property graph
    """
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'rewrite_delegations') and
                callable(subclass.rewrite_delegations) or NotImplemented)

    @abstractmethod
    def rewrite_delegations(self, *, real_adm_id: str = None) -> None:
        """
        Rewrite label and capacity delegations on all nodes to be dictionaries
        referenced by ADM graph id. Note that external code should
        not interact with delegations on ADM graphs.
        Sometimes ADMs are cloned into temporary graphs so the method provides
        a way to pass original ADM id as an option.
        :param real_adm_id:
        :return:
        """
