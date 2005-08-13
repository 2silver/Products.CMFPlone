#
# Skeleton PloneTestCase
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Products.CMFPlone.tests import PloneTestCase

from DateTime import DateTime


class TestDateIndexRanges(PloneTestCase.PloneTestCase):

    def afterSetUp(self):
        self.catalog = self.portal.portal_catalog
        self.folder.invokeFactory('Document', 'doc1', title='Foo')

    def testLoWatermark(self):
        self.folder.doc1.setExpirationDate(DateTime(-2113, 0))
        self.folder.doc1.reindexObject()

    def testHiWatermark(self):
        self.folder.doc1.setExpirationDate(DateTime(4008, 0))
        self.folder.doc1.reindexObject()

    def testUnderflow(self):
        self.folder.doc1.setExpirationDate(DateTime(-2114, 0))
        # No OverflowError due to monkey patch
        #self.assertRaises(OverflowError, self.folder.doc1.reindexObject)
        self.folder.doc1.reindexObject()

    def testOverflow(self):
        self.folder.doc1.setExpirationDate(DateTime(4009, 0))
        # No OverflowError due to monkey patch
        #self.assertRaises(OverflowError, self.folder.doc1.reindexObject)
        self.folder.doc1.reindexObject()

    def testDRIUnderflow(self):
        self.folder.doc1.setEffectiveDate(DateTime(-2114, 0))
        # No OverflowError due to monkey patch
        #self.assertRaises(OverflowError, self.folder.doc1.reindexObject)
        self.folder.doc1.reindexObject()

    def testDRIOverflow(self):
        self.folder.doc1.setEffectiveDate(DateTime(4009, 0))
        # No OverflowError due to monkey patch
        #self.assertRaises(OverflowError, self.folder.doc1.reindexObject)
        self.folder.doc1.reindexObject()


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestDateIndexRanges))
    return suite

if __name__ == '__main__':
    framework()
