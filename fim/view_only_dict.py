from collections.abc import Mapping, Iterator


class ViewOnlyDict(Mapping):
    """
    Provides a view-only access to a dictionary
    """

    def __init__(self, d):
        self.__dict = d

    def __iter__(self) -> Iterator:
        return self.__dict.__iter__()

    def __len__(self) -> int:
        return self.__dict.__len__()

    def __getitem__(self, k):
        return self.__dict.__getitem__(k)

    def __repr__(self):
        return self.__dict.__repr__()

    def __str__(self):
        return self.__dict.__str__()

    def __hash__(self):
        return self.__dict.__hash__()