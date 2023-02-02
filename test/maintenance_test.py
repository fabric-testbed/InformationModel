import unittest

from fim.slivers.maintenance_mode import MaintenanceInfo, MaintenanceEntry, \
    MaintenanceState, MaintenanceModeException
from datetime import datetime, timedelta


class TestMaintenance(unittest.TestCase):

    def test_maintenance(self):
        a = MaintenanceInfo()
        a.add(name='node1', minfo=MaintenanceEntry(MaintenanceState.Active))
        mi = MaintenanceEntry(MaintenanceState.PreMaint, deadline=datetime.now())
        a.add(name='node111', minfo=mi)
        a.add(name='node112', minfo=MaintenanceEntry(MaintenanceState.Maint, deadline=datetime.now(),
                                                     expected_end=datetime.now() + timedelta(days=1)))
        with self.assertRaises(MaintenanceModeException):
            # can't serialize unfinalized object
            a.to_json()

        a.finalize()
        j = a.to_json()
        b = MaintenanceInfo.from_json(j)

        self.assertEqual(a.get('node1'), b.get('node1'))
        self.assertEqual(a.get('node111'), b.get('node111'))
        self.assertEqual(a.get('node112'), b.get('node112'))

        self.assertIn('node111', a.list_names())
        self.assertIn(('node111', mi),
                      a.list_details())

        #for i in a.iter():
        #    print(i)

        c = a.copy()
        self.assertEqual(a.get('node1'), c.get('node1'))
        self.assertEqual(a.get('node111'), c.get('node111'))
        self.assertEqual(a.get('node112'), c.get('node112'))

        with self.assertRaises(MaintenanceModeException):
            # can't serialize unfinalized object
            # copy constructor doesn't finalize
            c.to_json()
