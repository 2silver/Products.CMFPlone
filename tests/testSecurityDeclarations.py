#
# Tests the security declarations Plone makes on resources
# for access by restricted code (aka PythonScripts)
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Products.CMFPlone.tests import PloneTestCase
from Products.CMFPlone.tests import dummy

from OFS.SimpleItem import SimpleItem
from AccessControl import Unauthorized
from ZODB.POSException import ConflictError
from Products.ZCTextIndex.ParseTree import ParseError


class RestrictedPythonTest(ZopeTestCase.ZopeTestCase):

    def addPS(self, id, params='', body=''):
        factory = self.folder.manage_addProduct['PythonScripts']
        factory.manage_addPythonScript(id)
        self.folder[id].ZPythonScript_edit(params, body)

    def check(self, psbody):
        self.addPS('ps', body=psbody)
        try:
            self.folder.ps()
        except (ImportError, Unauthorized), e:
            self.fail(e)

    def checkUnauthorized(self, psbody):
        self.addPS('ps', body=psbody)
        try:
            self.folder.ps()
        except (AttributeError, Unauthorized):
            pass


class TestSecurityDeclarations(RestrictedPythonTest):

    # NOTE: This test case is a bit hairy. Security declarations
    # "stick" once a module has been imported into the restricted
    # environment. Therefore the tests are not truly independent.
    # Be careful when adding new tests to this class.

    def testImport_LOG(self):
        self.check('from zLOG import LOG')

    def testAccess_LOG(self):
        self.check('import zLOG;'
                   'print zLOG.LOG')

    def testImport_INFO(self):
        self.check('from zLOG import INFO')

    def testAccess_INFO(self):
        self.check('import zLOG;'
                   'print zLOG.INFO')

    def testImport_translate_wrapper(self):
        self.check('from Products.CMFPlone.PloneUtilities import translate_wrapper')

    def testAccess_translate_wrapper(self):
        self.check('import Products.CMFPlone.PloneUtilities;'
                   'print Products.CMFPlone.PloneUtilities.translate_wrapper')

    def testImport_localized_time(self):
        self.check('from Products.CMFPlone.PloneUtilities import localized_time')

    def testAccess_localized_time(self):
        self.check('import Products.CMFPlone.PloneUtilities;'
                   'print Products.CMFPlone.PloneUtilities.localized_time')

    def testImport_IndexIterator(self):
        self.check('from Products.CMFPlone import IndexIterator')

    def testAccess_IndexIterator(self):
        self.check('from Products import CMFPlone;'
                   'print CMFPlone.IndexIterator')

    def testUse_IndexIterator(self):
        self.check('from Products.CMFPlone import IndexIterator;'
                   'print IndexIterator().next')

    def testImport_ObjectMoved(self):
        self.check('from Products.CMFCore.WorkflowCore import ObjectMoved')

    def testAccess_ObjectMoved(self):
        self.check('from Products.CMFCore import WorkflowCore;'
                   'print WorkflowCore.ObjectMoved')

    def testUse_ObjectMoved(self):
        self.check('from Products.CMFCore.WorkflowCore import ObjectMoved;'
                   'print ObjectMoved("foo").getResult')

    def testImport_ObjectDeleted(self):
        self.check('from Products.CMFCore.WorkflowCore import ObjectDeleted')

    def testAccess_ObjectDeleted(self):
        self.check('from Products.CMFCore import WorkflowCore;'
                   'print WorkflowCore.ObjectDeleted')

    def testUse_ObjectDeleted(self):
        self.check('from Products.CMFCore.WorkflowCore import ObjectDeleted;'
                   'print ObjectDeleted().getResult')

    def testImport_WorkflowException(self):
        self.check('from Products.CMFCore.WorkflowCore import WorkflowException')

    def testAccess_WorkflowException(self):
        self.check('from Products.CMFCore import WorkflowCore;'
                   'print WorkflowCore.WorkflowException')

    def testUse_WorkflowException(self):
        self.check('from Products.CMFCore.WorkflowCore import WorkflowException;'
                   'print WorkflowException().args')

    def testImport_Batch(self):
        self.check('from Products.CMFPlone import Batch')

    def testAccess_Batch(self):
        self.check('from Products import CMFPlone;'
                   'print CMFPlone.Batch')

    def testUse_Batch(self):
        self.check('from Products.CMFPlone import Batch;'
                   'print Batch([], 0).nexturls')

    def testImport_transaction_note(self):
        self.check('from Products.CMFPlone import transaction_note')

    def testAccess_transaction_note(self):
        self.check('import Products.CMFPlone;'
                   'print Products.CMFPlone.transaction_note')

    def testImport_listPolicies(self):
        self.check('from Products.CMFPlone.Portal import listPolicies')

    def testAccess_listPolicies(self):
        self.check('import Products.CMFPlone.Portal;'
                   'print Products.CMFPlone.Portal.listPolicies')

    def testImport_base_hasattr(self):
        self.check('from Products.CMFPlone import base_hasattr')

    def testAccess_base_hasattr(self):
        self.check('import Products.CMFPlone;'
                   'print Products.CMFPlone.base_hasattr')

    def testImport_Unauthorized(self):
        self.check('from AccessControl import Unauthorized')

    def testAccess_Unauthorized(self):
        self.check('import AccessControl;'
                   'print AccessControl.Unauthorized')

    def testImport_ConflictError(self):
        self.check('from ZODB.POSException import ConflictError')

    def testAccess_ConflictError(self):
        self.check('import ZODB.POSException;'
                   'print ZODB.POSException.ConflictError')

    def testRaise_ConflictError(self):
        self.assertRaises(ConflictError, 
            self.check, 'from ZODB.POSException import ConflictError;'
                        'raise ConflictError')

    def testCatch_ConflictErrorRaisedByRestrictedCode(self):
        try:
            self.check('''
from ZODB.POSException import ConflictError
try: raise ConflictError
except ConflictError: pass
''')
        except Exception, e:
            self.fail('Failed to catch: %s %s (module %s)' %
                      (e.__class__.__name__, e, e.__module__))

    def testCatch_ConflictErrorRaisedByPythonModule(self):
        self.folder._setObject('raiseConflictError', dummy.Raiser(ConflictError))
        try:
            self.check('''
from ZODB.POSException import ConflictError
try: context.raiseConflictError()
except ConflictError: pass
''')
        except Exception, e:
            self.fail('Failed to catch: %s %s (module %s)' %
                      (e.__class__.__name__, e, e.__module__))

    def testImport_getToolByName(self):
        self.check('from Products.CMFCore.utils import getToolByName')

    def testAccess_getToolByName(self):
        # XXX: Note that this is NOT allowed!
        self.checkUnauthorized('from Products.CMFCore import utils;'
                               'print utils.getToolByName')

    def testUse_getToolByName(self):
        self.app.manage_addFolder('portal_membership') # Fake a portal tool
        self.check('from Products.CMFCore.utils import getToolByName;'
                   'print getToolByName(context, "portal_membership")')

    def testImport_ParseError(self):
        self.check('from Products.ZCTextIndex.ParseTree import ParseError')

    def testAccess_ParseError(self):
        self.check('import Products.ZCTextIndex.ParseTree;'
                   'print Products.ZCTextIndex.ParseTree.ParseError')

    def testCatch_ParseErrorRaisedByPythonModule(self):
        self.folder._setObject('raiseParseError', dummy.Raiser(ParseError))
        try:
            self.check('''
from Products.ZCTextIndex.ParseTree import ParseError
try: context.raiseParseError()
except ParseError: pass
''')
        except Exception, e:
            self.fail('Failed to catch: %s %s (module %s)' %
                      (e.__class__.__name__, e, e.__module__))


class TestAcquisitionMethods(RestrictedPythonTest):

    def test_aq_explicit(self):
        self.check('print context.aq_explicit')

    def test_aq_parent(self):
        self.check('print context.aq_parent')

    def test_aq_inner(self):
        self.check('print context.aq_inner')

    def test_aq_inner_aq_parent(self):
        self.check('print context.aq_inner.aq_parent')

    def test_aq_self(self):
        self.checkUnauthorized('print context.aq_self')

    def test_aq_base(self):
        self.checkUnauthorized('print context.aq_base')

    def test_aq_acquire(self):
        self.checkUnauthorized('print context.aq_acquire')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestSecurityDeclarations))
    suite.addTest(makeSuite(TestAcquisitionMethods))
    return suite

if __name__ == '__main__':
    framework()
