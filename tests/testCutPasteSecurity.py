#
# Tests security of cut/paste operations
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Products.CMFPlone.tests import PloneTestCase

from AccessControl import Unauthorized, getSecurityManager
from OFS.CopySupport import CopyError
from Acquisition import aq_base


class TestCutPasteSecurity(PloneTestCase.PloneTestCase):

    def afterSetUp(self):
        self.portal.acl_users._doAddUser('user1', 'secret', ['Member'], [])
        self.portal.acl_users._doAddUser('user2', 'secret', ['Member'], [])
        self.membership = self.portal.portal_membership
        self.createMemberarea('user1')
        self.createMemberarea('user2')

    def testRenameMemberContent(self):
        self.login('user1')
        folder = self.membership.getHomeFolder('user1')
        folder.invokeFactory('Document', id='testrename')

        # We need to commit here so that _p_jar isn't None and move
        # will work
        get_transaction().commit(1)
        folder.manage_renameObject('testrename', 'new')
        self.failIf(hasattr(aq_base(folder), 'testrename'))
        self.failUnless(hasattr(aq_base(folder), 'new'))

    def testRenameOtherMemberContentFails(self):
        self.login('user1')
        src = self.membership.getHomeFolder('user1')
        src.invokeFactory('Document', id='testrename')

        self.login('user2')
        folder = self.membership.getHomeFolder('user1')
        self.assertRaises(CopyError, folder.manage_renameObject, 'testrename', 'bad')

    def testCopyMemberContent(self):
        self.login('user1')
        src = self.membership.getHomeFolder('user1')
        src.invokeFactory('Document', id='testcopy')
        dest = self.membership.getPersonalFolder('user1')
        dest.manage_pasteObjects(src.manage_copyObjects('testcopy'))

        # After a copy/paste, they should *both* have a copy
        self.failUnless(hasattr(aq_base(src), 'testcopy'))
        self.failUnless(hasattr(aq_base(dest), 'testcopy'))

    def testCopyOtherMemberContent(self):
        self.login('user1')
        src = self.membership.getHomeFolder('user1')
        src.invokeFactory('Document', id='testcopy')

        self.login('user2')
        dest = self.membership.getPersonalFolder('user2')
        dest.manage_pasteObjects(src.manage_copyObjects('testcopy'))
        # After a copy/paste, they should *both* have a copy
        self.failUnless(hasattr(aq_base(src), 'testcopy'))
        self.failUnless(hasattr(aq_base(dest), 'testcopy'))

    def testCutMemberContent(self):
        self.login('user1')
        src = self.membership.getHomeFolder('user1')
        src.invokeFactory('Document', id='testcut')

        # We need to commit here so that _p_jar isn't None and move
        # will work
        get_transaction().commit(1)

        dest = self.membership.getPersonalFolder('user1')
        dest.manage_pasteObjects(src.manage_cutObjects('testcut'))

        # After a cut/paste, only destination has a copy
        self.failIf(hasattr(aq_base(src), 'testcut'))
        self.failUnless(hasattr(aq_base(dest), 'testcut'))

    def testCutOtherMemberContent(self):
        self.login('user1')
        src = self.membership.getHomeFolder('user1')
        src.invokeFactory('Document', id='testcut')

        # We need to commit here so that _p_jar isn't None and move
        # will work
        get_transaction().commit(1)

        self.login('user2')
        self.assertRaises(Unauthorized, src.restrictedTraverse, 'manage_cutObjects')

    def test_Bug2183_PastingIntoFolderFailsForNotAllowedContentTypes(self):
        # XXX This test is related to the '_verifyObjectPaste' change
        # in PloneFolder.py. With the move of the bug fix to CMFCore
        # this test will move also and could the be removed from here.
        # http://plone.org/collector/2183

        # add the document to be copy and pasted later
        self.folder.invokeFactory('Document', 'doc')

        # add the folder where we try to paste the document later
        self.folder.invokeFactory('Folder', 'subfolder')
        subfolder = self.folder.subfolder

        # now disallow adding Document globaly
        types = self.portal.portal_types
        types.Document.manage_changeProperties(global_allow=0)

        # copy and pasting the object into the subfolder should raise
        # a ValueError.
        self.assertRaises(
            ValueError,
            subfolder.manage_pasteObjects,
            self.folder.manage_copyObjects(ids=['doc'])
        )

    def test_Bug2183_PastingIntoPortalFailsForNotAllowedContentTypes(self):
        # XXX This test is related to the '_verifyObjectPaste' change
        # in PloneFolder.py. With the move of the bug fix to CMFCore
        # this test will move also and could the be removed from here.
        # http://plone.org/collector/2183

        # add the document to be copy and pasted later
        self.folder.invokeFactory('Document', 'doc')

        # now disallow adding Document globaly
        types = self.portal.portal_types
        types.Document.manage_changeProperties(global_allow=0)

        # need to be manager to paste into portal
        self.setRoles(['Manager'])

        # copy and pasting the object into the portal should raise
        # a ValueError.
        self.assertRaises(
            ValueError,
            self.portal.manage_pasteObjects,
            self.folder.manage_copyObjects(ids=['doc'])
        )


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestCutPasteSecurity))
    return suite

if __name__ == '__main__':
    framework()
