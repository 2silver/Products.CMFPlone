#
# Tests for GRUF's GroupDataTool
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Products.CMFPlone.tests import PloneTestCase
from Acquisition import aq_base

from Products.GroupUserFolder.GroupUserFolder import GroupUserFolder
from Products.GroupUserFolder.GroupUserFolder import manage_addGroupUserFolder
from Products.GroupUserFolder.GroupDataTool import GroupDataTool
from Products.GroupUserFolder.GroupsTool import GroupsTool

default_user = PloneTestCase.default_user

def sortTuple(t):
    l = list(t)
    l.sort()
    return tuple(l)

class TestGroupDataTool(PloneTestCase.PloneTestCase):

    def afterSetUp(self):
        self.acl_users = self.portal.acl_users
        self.groups = self.portal.portal_groups
        self.groupdata = self.portal.portal_groupdata
        self.prefix = self.acl_users.getGroupPrefix()
        self.groups.groupWorkspacesCreationFlag = 0
        self.groups.addGroup('foo', '', [], [])
        # MUST reset _v_ attributes!
        self.groupdata._v_temps = None

    def testWrapGroup(self):
        g = self.acl_users.getGroup(self.prefix+'foo')
        self.assertEqual(g.__class__.__name__, 'GRUFUser')
        g = self.groupdata.wrapGroup(g)
        self.assertEqual(g.__class__.__name__, 'GroupData')
        self.assertEqual(g.aq_parent.__class__.__name__, 'GRUFUser')
        self.assertEqual(g.aq_parent.aq_parent.__class__.__name__, 'GroupUserFolder')

    def testRegisterGroupData(self):
        g = self.groups.getGroupById('foo')
        self.assertEqual(len(self.groupdata._members), 0)
        self.groupdata.registerGroupData(aq_base(g), g.getId())
        self.assertEqual(len(self.groupdata._members), 1)


class TestGroupData(PloneTestCase.PloneTestCase):

    def afterSetUp(self):
        self.membership = self.portal.portal_membership
        self.memberdata = self.portal.portal_memberdata
        self.acl_users = self.portal.acl_users
        self.groups = self.portal.portal_groups
        self.groupdata = self.portal.portal_groupdata
        self.prefix = self.acl_users.getGroupPrefix()
        self.groups.groupWorkspacesCreationFlag = 0
        self.groups.addGroup('foo', '', [], [])
        # MUST reset _v_ attributes!
        self.memberdata._v_temps = None
        self.groupdata._v_temps = None

    def testGroupNotifyModified(self):
        g = self.groups.getGroupById('foo')
        self.assertEqual(len(self.groupdata._members), 0)
        self.failIfEqual(getattr(g, '_tool', None), None)
        g.notifyModified()
        self.assertEqual(len(self.groupdata._members), 1)
        self.assertEqual(getattr(g, '_tool', None), None)

    def testMemberNotifyModified(self):
        # For reference
        m = self.membership.getMemberById(default_user)
        self.assertEqual(len(self.memberdata._members), 0)
        self.failIfEqual(getattr(m, '_tool', None), None)
        m.notifyModified()
        self.assertEqual(len(self.memberdata._members), 1)
        self.assertEqual(getattr(m, '_tool', None), None)

    def testGetGroup(self):
        g = self.groups.getGroupById('foo')
        self.assertEqual(g.__class__.__name__, 'GroupData')
        g = g.getGroup()
        self.assertEqual(g.__class__.__name__, 'GRUFUser')

    def testGetTool(self):
        g = self.groups.getGroupById('foo')
        self.assertEqual(g.getTool().getId(), 'portal_groupdata')

    def testGetGroupMembers(self):
        g = self.groups.getGroupById('foo')
        self.acl_users._updateUser(default_user, groups=['foo'])
        self.assertEqual(g.getGroupMembers()[0].getId(), default_user)

    def testGroupMembersAreWrapped(self):
        g = self.groups.getGroupById('foo')
        self.acl_users._updateUser(default_user, groups=['foo'])
        ms = g.getGroupMembers()
        self.assertEqual(ms[0].__class__.__name__, 'MemberData')
        self.assertEqual(ms[0].aq_parent.__class__.__name__, 'GRUFUser')
        self.assertEqual(ms[0].aq_parent.aq_parent.__class__.__name__, 'GroupUserFolder')

    def testAddMember(self):
        g = self.groups.getGroupById('foo')
        g.addMember(default_user)
        self.assertEqual(g.getGroupMembers()[0].getId(), default_user)

    def testRemoveMember(self):
        g = self.groups.getGroupById('foo')
        g.addMember(default_user)
        g.removeMember(default_user)
        self.assertEqual(len(g.getGroupMembers()), 0)

    #def testSetProperties(self):
    #    # XXX: ERROR!
    #    g = self.groups.getGroupById('foo')
    #    g.setProperties(email='foo@bar.com')
    #    gd = self.groupdata._members[self.prefix+'foo']
    #    self.assertEqual(gd.email, 'foo@bar.com')

    def testSetGroupProperties(self):
        g = self.groups.getGroupById('foo')
        g.setGroupProperties({'email': 'foo@bar.com'})
        gd = self.groupdata._members[g.getId()]
        self.assertEqual(gd.email, 'foo@bar.com')

    def testSetMemberProperties(self):
        # For reference
        m = self.membership.getMemberById(default_user)
        m.setMemberProperties({'email': 'foo@bar.com'})
        md = self.memberdata._members[m.getId()]
        self.assertEqual(md.email, 'foo@bar.com')

    def testGetProperty(self):
        g = self.groups.getGroupById('foo')
        g.setGroupProperties({'email': 'foo@bar.com'})
        self.assertEqual(g.getProperty('email'), 'foo@bar.com')
        self.assertEqual(g.getProperty('id'), self.prefix+'foo')

    def testGetGroupName(self):
        g = self.groups.getGroupById('foo')
        self.assertEqual(g.getGroupName(), 'foo')

    def testGetGroupId(self):
        g = self.groups.getGroupById('foo')
        self.assertEqual(g.getGroupId(), self.prefix+'foo')

    def testGetRoles(self):
        g = self.groups.getGroupById('foo')
        self.assertEqual(g.getRoles(), ('Authenticated',))
        self.acl_users._updateGroup(g.getId(), roles=['Member'])
        g = self.groups.getGroupById('foo')
        self.assertEqual(sortTuple(g.getRoles()), ('Authenticated', 'Member'))

    def testGetRolesInContext(self):
        g = self.groups.getGroupById('foo')
        self.assertEqual(g.getRolesInContext(self.folder), ('Authenticated',))
        self.folder.manage_setLocalRoles(g.getId(), ['Owner'])
        self.assertEqual(sortTuple(g.getRolesInContext(self.folder)), ('Authenticated', 'Owner'))

    def testGetDomains(self):
        g = self.groups.getGroupById('foo')
        self.assertEqual(g.getDomains(), ())

    def testHasRole(self):
        g = self.groups.getGroupById('foo')
        self.acl_users._updateGroup(g.getId(), roles=['Member'])
        g = self.groups.getGroupById('foo')
        self.failUnless(g.has_role('Member'))


if __name__ == '__main__':
    framework(verbosity=1)
else:
    from unittest import TestSuite, makeSuite
    def test_suite():
        suite = TestSuite()
        suite.addTest(makeSuite(TestGroupDataTool))
        suite.addTest(makeSuite(TestGroupData))
        return suite
