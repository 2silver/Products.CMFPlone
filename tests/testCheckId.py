#
# Test check_id script
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Products.CMFPlone.tests import PloneTestCase
from Products.CMFPlone.tests import dummy

from AccessControl import getSecurityManager
from AccessControl import Unauthorized
from ZODB.POSException import ConflictError


class TestCheckId(PloneTestCase.PloneTestCase):
    '''Tests the check_id script'''

    def testGoodId(self):
        r = self.folder.check_id('foo')
        self.assertEqual(r, None)   # success

    def testEmptyId(self):
        r = self.folder.check_id('')
        self.assertEqual(r, None)   # success

    def testRequiredId(self):
        r = self.folder.check_id('', required=1)
        self.assertEqual(r, "Please enter a name.")

    def testAlternativeId(self):
        r = self.folder.check_id('', alternative_id='foo')
        self.assertEqual(r, None)   # success

    def testBadId(self):
        r = self.folder.check_id('=')
        self.assertEqual(r, "'=' is not a legal name.")

    def testCatalogIndex(self):
        # XXX: tripwire
        have_permission = self.portal.portal_membership.checkPermission
        self.failUnless(have_permission('Search ZCatalog', self.portal.portal_catalog),
                        'Expected permission "Search ZCatalog"')

        r = self.folder.check_id('created')
        self.assertEqual(r, "'created' is reserved.")

    def testCollision(self):
        self.folder._setObject('foo', dummy.Item('foo'))
        self.folder._setObject('bar', dummy.Item('bar'))
        r = self.folder.foo.check_id('bar')
        self.assertEqual(r, "There is already an item named 'bar' in this folder.")

    def testTempObjectCollision(self):
        foo = self.folder.restrictedTraverse('portal_factory/Document/foo')
        self.folder._setObject('bar', dummy.Item('bar'))
        r = foo.check_id('bar')
        self.assertEqual(r, "There is already an item named 'bar' in this folder.")

    def testReservedId(self):
        self.folder._setObject('foo', dummy.Item('foo'))
        r = self.folder.foo.check_id('portal_catalog')
        self.assertEqual(r, "'portal_catalog' is reserved.")

    def testInvalidId(self):
        self.folder._setObject('foo', dummy.Item('foo'))
        r = self.folder.foo.check_id('_foo')
        self.assertEqual(r, "'_foo' is reserved.")

    def testContainerHook(self):
        # Container may have a checkValidId method; make sure it is called
        self.folder._setObject('checkValidId', dummy.Raiser(dummy.Error))
        self.folder._setObject('foo', dummy.Item('foo'))
        r = self.folder.foo.check_id('whatever')
        self.assertEqual(r, "'whatever' is reserved.")

    def testContainerHookRaisesUnauthorized(self):
        # check_id should not swallow Unauthorized errors raised by hook
        self.folder._setObject('checkValidId', dummy.Raiser(Unauthorized))
        self.folder._setObject('foo', dummy.Item('foo'))
        self.assertRaises(Unauthorized, self.folder.foo.check_id, 'whatever')

    def testContainerHookRaisesConflictError(self):
        # check_id should not swallow ConflictErrors raised by hook
        self.folder._setObject('checkValidId', dummy.Raiser(ConflictError))
        self.folder._setObject('foo', dummy.Item('foo'))
        self.assertRaises(ConflictError, self.folder.foo.check_id, 'whatever')

    def testMissingUtils(self):
        # check_id should not bomb out if the plone_utils tool is missing
        self.portal._delObject('plone_utils')
        r = self.folder.check_id('foo')
        self.assertEqual(r, None)   # success

    def testMissingCatalog(self):
        # check_id should not bomb out if the portal_catalog tool is missing
        self.portal._delObject('portal_catalog')
        r = self.folder.check_id('foo')
        self.assertEqual(r, None)   # success

    def testMissingFactory(self):
        # check_id should not bomb out if the portal_factory tool is missing
        self.portal._delObject('portal_factory')
        r = self.folder.check_id('foo')
        self.assertEqual(r, None)   # success

    def testCatalogIndexSkipped(self):
        # Note that the check is skipped when we don't have 
        # the "Search ZCatalogs" permission.
        self.portal.manage_permission('Search ZCatalog', ['Manager'], acquire=0)

        r = self.folder.check_id('created')
        self.assertEqual(r, None)   # success

    def testCollisionSkipped(self):
        # Note that check is skipped when we don't have 
        # the "Access contents information" permission.
        self.folder.manage_permission('Access contents information', ['Manager'], acquire=0)

        self.folder._setObject('foo', dummy.Item('foo'))
        self.folder._setObject('bar', dummy.Item('bar'))
        r = self.folder.foo.check_id('bar')
        self.assertEqual(r, None)   # success

    def testReservedIdSkipped(self):
        # Note that the check is skipped when we don't have 
        # the "Add portal content" permission.
        self.folder.manage_permission('Add portal content', ['Manager'], acquire=0)

        self.folder._setObject('foo', dummy.Item('foo'))
        r = self.folder.foo.check_id('portal_catalog')
        self.assertEqual(r, None)   # success

    def testInvalidIdSkipped(self):
        # Note that the check is skipped when we don't have 
        # the "Add portal content" permission.
        self.folder.manage_permission('Add portal content', ['Manager'], acquire=0)

        self.folder._setObject('foo', dummy.Item('foo'))
        r = self.folder.foo.check_id('_foo')
        self.assertEqual(r, None)   # success


# XXX: This is absolutely weird

class TestCrazyRoles(PloneTestCase.PloneTestCase):

    def afterSetUp(self):
        self.membership = self.portal.portal_membership

    def getPermissionsOfRole(self, role, context=None):
        if context is None:
            context = self.portal
        perms = context.permissionsOfRole(role)
        return [p['name'] for p in perms if p['selected']]
        
    def assertPermissionsOfRole(self, permissions, role, context=None):
        lhs = list(permissions)[:]
        lhs.sort()
        rhs = self.getPermissionsOfRole(role, context)
        rhs.sort()
        self.assertEqual(lhs, rhs)

    def test_crazyRoles_0(self):
        # Permission assignments should be reset
        perms = self.getPermissionsOfRole('Anonymous', self.app)
        for perm in ['Access contents information', 'View', 'Query Vocabulary', 'Search ZCatalog']:
            if perm not in perms:
                self.fail('Expected permission "%s"' % perm)

    def test_crazyRoles_1(self):
        # Permission assignments should be reset
        self.app.manage_role('Anonymous', ['View'])
        self.assertPermissionsOfRole(['View'], 'Anonymous', self.app)
        self.logout()
        self.failIf(getSecurityManager().checkPermission('Access contents information', self.app))
        self.failIf(self.membership.checkPermission('Access contents information', self.app))
        
    def test_crazyRoles_2(self):
        # Permission assignments should be reset
        try:
            self.assertPermissionsOfRole(['View'], 'Anonymous', self.app)
        except self.failureException:
            pass

    def test_crazyRoles_3(self):
        # Permission assignments should be reset
        self.logout()
        self.failUnless(getSecurityManager().checkPermission('Access contents information', self.app))
        self.failUnless(self.membership.checkPermission('Access contents information', self.app))

    def test_crazyRoles_4(self):
        # Permission assignments should be reset
        perms = self.getPermissionsOfRole('Anonymous', self.app)
        for perm in ['Access contents information', 'View', 'Query Vocabulary', 'Search ZCatalog']:
            if perm not in perms:
                self.fail('Expected permission "%s"' % perm)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    #suite.addTest(makeSuite(TestCrazyRoles))
    suite.addTest(makeSuite(TestCheckId))
    return suite

if __name__ == '__main__':
    framework()
