import unittest

import fim.user as fu


def load(file_name: str):

    t = fu.ExperimentTopology()
    t.load(file_name=file_name)
    return t


class LoadTests(unittest.TestCase):

    def testNetworkXLoad(self):
        """
        Test for a stupid case where loading silently failed on duplicate graph IDs
        """
        print('')
        t1 = load(file_name="test/before.graphml")
        print(f"{t1.nodes['n2'].management_ip=}")
        t2 = load(file_name="test/after.graphml")
        print(f"{t2.nodes['n2'].management_ip=}")
        self.assertEqual(str(t2.nodes['n2'].management_ip), '128.163.179.51', "No management IP address found")