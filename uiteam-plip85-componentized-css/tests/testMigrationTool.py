#
# MigrationTool tests
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Products.CMFPlone.tests import PloneTestCase


class TestMigrationTool(PloneTestCase.PloneTestCase):

    def afterSetUp(self):
        self.migration = self.portal.portal_migration

    def testMigrationFinished(self):
        self.assertEqual(self.migration.getInstanceVersion(),
                         self.migration.getFileSystemVersion(),
                         'Migration failed')

    def testMigrationNeedsUpgrading(self):
        self.failIf(self.migration.needUpgrading(),
                    'Migration needs upgrading')

    def testMigrationNeedsUpdateRole(self):
        self.failIf(self.migration.needUpdateRole(),
                    'Migration needs role update')

    def testMigrationNeedsRecatalog(self):
        self.failIf(self.migration.needRecatalog(),
                    'Migration needs recataloging')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestMigrationTool))
    return suite

if __name__ == '__main__':
    framework()
