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
import dataclasses
from typing import List, Tuple, Any, Dict
import enum
from dataclasses import dataclass
from datetime import datetime, timedelta, date, time, timezone
import json


class MaintenanceState(enum.Enum):
    Active = enum.auto()
    PreMaint = enum.auto()
    Maint = enum.auto()
    Unknown = enum.auto()

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    @classmethod
    def from_string(cls, s: str):
        for ms in MaintenanceState:
            if s == ms.name:
                return cls(ms)
        return None


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, MaintenanceState):
            return str(o)
        if isinstance(o, (datetime, date, time)):
            return o.isoformat()
        return super().default(o)


@dataclass(eq=True)
class MaintenanceEntry:
    state: MaintenanceState
    deadline: datetime = None # when it starts
    expected_end: datetime = None # how long it may be

    def __init__(self, state: MaintenanceState or str,
                 deadline: datetime or str or None = None,
                 expected_end: datetime or str or None = None):
        if isinstance(state, MaintenanceState):
            self.state = state
        else:
            self.state = MaintenanceState.from_string(state)

        if isinstance(deadline, datetime):
            self.deadline = deadline
        elif deadline:
            self.deadline = datetime.fromisoformat(deadline)

        if isinstance(expected_end, datetime):
            self.expected_end = expected_end
        elif expected_end:
            self.expected_end = datetime.fromisoformat(expected_end)


class MaintenanceModeException(Exception):
    def __init(self, msg: str):
        super().__init__(msg)


# ABQM maintenance information is a dictionary
class MaintenanceInfo:

    def __init__(self):
        self._nodes = dict()
        # prevent modifications
        self._lock = False

    def _set(self, d: Dict):
        self._nodes = d

    def finalize(self):
        """
        Prevent further modifications - used after the object is
        assigned to a property
        """
        self._lock = True

    def add(self, name: str, minfo: MaintenanceEntry) -> None:
        """
        Add entry
        """
        if self._lock:
            raise MaintenanceModeException("Unable to modify a finalized object, recreate and reassign")
        self._nodes[name] = minfo

    def get(self, name: str) -> MaintenanceEntry or None:
        return self._nodes.get(name)

    def rem(self, name: str) -> None:
        """
        Remove entry
        """
        if self._lock:
            raise MaintenanceModeException("Unable to modify a finalized object, recreate and reassign")
        self._nodes.pop(name)

    def pop(self, name: str) -> MaintenanceEntry:
        """
        Pop an entry returning maintenance info
        """
        if self._lock:
            raise MaintenanceModeException("Unable to modify a finalized object, recreate and reassign")
        return self._nodes.pop(name)

    def to_json(self) -> str:
        """
        Convert structure to JSON
        """
        if not self._lock:
            raise MaintenanceModeException("Object should be finalized prior to serializing")
        return json.dumps(self._nodes, cls=EnhancedJSONEncoder)

    def copy(self):
        """
        Copy an instance of the object but don't finalize
        """
        t = MaintenanceInfo()
        t._nodes = self._nodes.copy()
        return t

    def list_names(self) -> List[str]:
        """
        List the names of the nodes in maintenance
        """
        return list(self._nodes.keys())

    def list_details(self) -> List[Tuple[str, Any]]:
        """
        Return a list of tuples with node name and maintenance state details
        """
        return list(self._nodes.copy().items())

    def iter(self):
        """
        Generate an item iterator on a finalized object, so you can do
        for i in minfo.iter():
          print(i)
        """
        if not self._lock:
            raise MaintenanceModeException("Object should be finalized prior to attempting iteration")
        for i in self._nodes.items():
            yield i

    @classmethod
    def from_json(cls, json_string: str):
        """
        Convert into structure from JSON
        """
        if json_string is None or len(json_string) == 0:
            return None
        o = json.loads(json_string)
        ret = cls()
        ret._set({k: MaintenanceEntry(**v) for (k, v) in o.items()})
        ret.finalize()
        return ret

    def __str__(self):
        return self.to_json()

