#
# Tests for migration components
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Products.CMFPlone.tests import PloneTestCase

from Products.CMFPlone.migrations.v2.two04_two05 import replaceFolderPropertiesWithEdit
from Products.CMFPlone.migrations.v2.two04_two05 import interchangeEditAndSharing
from Products.CMFPlone.migrations.v2.two04_two05 import addFolderListingActionToTopic

from Products.CMFPlone.migrations.v2_1.alphas import addFullScreenAction
from Products.CMFPlone.migrations.v2_1.alphas import addFullScreenActionIcon
from Products.CMFPlone.migrations.v2_1.alphas import addVisibleIdsSiteProperty
from Products.CMFPlone.migrations.v2_1.alphas import deleteVisibleIdsMemberProperty
from Products.CMFPlone.migrations.v2_1.alphas import switchPathIndex
from Products.CMFPlone.migrations.v2_1.alphas import addGetObjPositionInParentIndex
from Products.CMFPlone.migrations.v2_1.alphas import addGetObjSizeMetadata
from Products.CMFPlone.migrations.v2_1.alphas import updateNavTreeProperties
from Products.CMFPlone.migrations.v2_1.alphas import addSitemapAction
from Products.CMFPlone.migrations.v2_1.alphas import reindexCatalog


class MigrationTest(PloneTestCase.PloneTestCase):

    def removeActionFromType(self, type_name, action_id):
        # Removes an action from a portal type
        tool = getattr(self.portal, 'portal_types')
        info = tool.getTypeInfo(type_name)
        typeob = getattr(tool, info.getId())
        actions = info.listActions()
        actions = [x for x in actions if x.id != action_id]
        typeob._actions = tuple(actions)

    def removeActionFromTool(self, action_id):
        # Removes an action from portal_actions
        tool = getattr(self.portal, 'portal_actions')
        actions = tool.listActions()
        actions = [x for x in actions if x.id != action_id]
        tool._actions = tuple(actions)

    def removeActionIconFromTool(self, action_id):
        # Removes an action icon from portal_actionicons
        tool = getattr(self.portal, 'portal_actionicons')
        try:
            tool.removeActionIcon('plone', action_id)
        except KeyError:
            pass # No icon associated

    def removeSiteProperty(self, property_id):
        # Removes a site property from portal_properties
        tool = getattr(self.portal, 'portal_properties')
        sheet = getattr(tool, 'site_properties')
        if sheet.hasProperty(property_id):
            sheet.manage_delProperties([property_id])

    def removeNavTreeProperty(self, property_id):
        # Removes a navtree property from portal_properties
        tool = getattr(self.portal, 'portal_properties')
        sheet = getattr(tool, 'navtree_properties')
        if sheet.hasProperty(property_id):
            sheet.manage_delProperties([property_id])


class TestMigrations_v2(MigrationTest):

    def afterSetUp(self):
        self.types = self.portal.portal_types

    def testReplaceFolderPropertiesWithEditNoFolder(self):
        # Should not fail if Folder type is missing
        self.types._delObject('Folder')
        replaceFolderPropertiesWithEdit(self.portal, [])

    def testReplaceFolderPropertiesWithEditNoEdit(self):
        # Should not fail if action is missing
        self.removeActionFromType('Folder', 'edit')
        replaceFolderPropertiesWithEdit(self.portal, [])

    def testInterchangeEditAndSharingNoFolder(self):
        # Should not fail if Folder type is missing
        self.types._delObject('Folder')
        interchangeEditAndSharing(self.portal, [])

    def testInterchangeEditAndSharingNoSharing(self):
        # Should not fail if action is missing
        self.removeActionFromType('Folder', 'local_roles')
        interchangeEditAndSharing(self.portal, [])

    def testInterchangeEditAndSharingNoEdit(self):
        # Should not fail if action is missing
        self.removeActionFromType('Folder', 'edit')
        interchangeEditAndSharing(self.portal, [])

    def testAddFolderListingToTopicNoTopic(self):
        # Should not fail if Topic type is missing
        self.types._delObject('Topic')
        addFolderListingActionToTopic(self.portal, [])


class TestMigrations_v2_1(MigrationTest):

    def afterSetUp(self):
        self.actions = self.portal.portal_actions
        self.icons = self.portal.portal_actionicons
        self.properties = self.portal.portal_properties
        self.memberdata = self.portal.portal_memberdata
        self.catalog = self.portal.portal_catalog

    def testAddFullScreenAction(self):
        # Should add the full_screen action
        self.removeActionFromTool('full_screen')
        addFullScreenAction(self.portal, [])
        self.failUnless('full_screen' in [x.id for x in self.actions.listActions()])

    def testAddFullScreenActionTwice(self):
        # Should not fail if migrated again
        self.removeActionFromTool('full_screen')
        addFullScreenAction(self.portal, [])
        addFullScreenAction(self.portal, [])
        self.failUnless('full_screen' in [x.id for x in self.actions.listActions()])

    def testAddFullScreenActionNoTool(self):
        # Should not fail if portal_actions is missing
        self.portal._delObject('portal_actions')
        addFullScreenAction(self.portal, [])

    def testAddFullScreenActionIcon(self):
        # Should add the full_screen action icon
        self.removeActionIconFromTool('full_screen')
        addFullScreenActionIcon(self.portal, [])
        self.failUnless('full_screen' in [x.getActionId() for x in self.icons.listActionIcons()])

    def testAddFullScreenActionIconTwice(self):
        # Should not fail if migrated again
        self.removeActionIconFromTool('full_screen')
        addFullScreenActionIcon(self.portal, [])
        addFullScreenActionIcon(self.portal, [])
        self.failUnless('full_screen' in [x.getActionId() for x in self.icons.listActionIcons()])

    def testAddFullScreenActionIconNoTool(self):
        # Should not fail if portal_actionicons is missing
        self.portal._delObject('portal_actionicons')
        addFullScreenActionIcon(self.portal, [])

    def testAddVisibleIdsSiteProperty(self):
        # Should add the visible_ids property
        self.removeSiteProperty('visible_ids')
        self.failIf(self.properties.site_properties.hasProperty('visible_ids'))
        addVisibleIdsSiteProperty(self.portal, [])
        self.failUnless(self.properties.site_properties.hasProperty('visible_ids'))

    def testAddVisibleIdsSitePropertyTwice(self):
        # Should not fail if migrated again
        self.removeSiteProperty('visible_ids')
        self.failIf(self.properties.site_properties.hasProperty('visible_ids'))
        addVisibleIdsSiteProperty(self.portal, [])
        addVisibleIdsSiteProperty(self.portal, [])
        self.failUnless(self.properties.site_properties.hasProperty('visible_ids'))

    def testAddVisibleIdsSitePropertyNoTool(self):
        # Should not fail if portal_properties is missing
        self.portal._delObject('portal_properties')
        addVisibleIdsSiteProperty(self.portal, [])

    def testAddVisibleIdsSitePropertyNoSheet(self):
        # Should not fail if site_properties is missing
        self.properties._delObject('site_properties')
        addVisibleIdsSiteProperty(self.portal, [])

    def testDeleteVisibleIdsMemberProperty(self):
        # Should delete the memberdata property
        if not self.memberdata.hasProperty('visible_ids'):
            self.memberdata.manage_addProperty('visible_ids', 0, 'boolean')
        self.failUnless(self.memberdata.hasProperty('visible_ids'))
        deleteVisibleIdsMemberProperty(self.portal, [])
        self.failIf(self.memberdata.hasProperty('visible_ids'))

    def testDeleteVisibleIdsMemberPropertyTwice(self):
        # Should not fail if migrated again
        if not self.memberdata.hasProperty('visible_ids'):
            self.memberdata.manage_addProperty('visible_ids', 0, 'boolean')
        self.failUnless(self.memberdata.hasProperty('visible_ids'))
        deleteVisibleIdsMemberProperty(self.portal, [])
        deleteVisibleIdsMemberProperty(self.portal, [])
        self.failIf(self.memberdata.hasProperty('visible_ids'))

    def testDeleteVisibleIdsMemberPropertyNoTool(self):
        # Should not fail if portal_memberdata is missing
        self.portal._delObject('portal_memberdata')
        deleteVisibleIdsMemberProperty(self.portal, [])

    def testSwitchPathIndex(self):
        # Should convert 'path' index to EPI
        self.catalog.delIndex('path')
        self.catalog.addIndex('path', 'FieldIndex')
        switchPathIndex(self.portal, [])
        index = self.catalog._catalog.getIndex('path')
        self.assertEqual(index.__class__.__name__, 'ExtendedPathIndex')

    def testSwitchPathIndexTwice(self):
        # Should not fail if migrated again
        self.catalog.delIndex('path')
        self.catalog.addIndex('path', 'FieldIndex')
        switchPathIndex(self.portal, [])
        switchPathIndex(self.portal, [])
        index = self.catalog._catalog.getIndex('path')
        self.assertEqual(index.__class__.__name__, 'ExtendedPathIndex')

    def testSwitchPathIndexNoCatalog(self):
        # Should not fail if portal_catalog is missing
        self.portal._delObject('portal_catalog')
        switchPathIndex(self.portal, [])

    def testSwitchPathIndexNoIndex(self):
        # Should not fail if path index is missing
        self.catalog.delIndex('path')
        switchPathIndex(self.portal, [])
        index = self.catalog._catalog.getIndex('path')
        self.assertEqual(index.__class__.__name__, 'ExtendedPathIndex')

    def testAddGetObjPositionInParentIndex(self):
        # Should add getObjPositionInParent index
        self.catalog.delIndex('getObjPositionInParent')
        addGetObjPositionInParentIndex(self.portal, [])
        index = self.catalog._catalog.getIndex('getObjPositionInParent')
        self.assertEqual(index.__class__.__name__, 'FieldIndex')

    def testAddGetObjPositionInParentIndexTwice(self):
        # Should not fail if migrated again
        self.catalog.delIndex('getObjPositionInParent')
        addGetObjPositionInParentIndex(self.portal, [])
        addGetObjPositionInParentIndex(self.portal, [])
        index = self.catalog._catalog.getIndex('getObjPositionInParent')
        self.assertEqual(index.__class__.__name__, 'FieldIndex')

    def testAddGetObjPositionInParentIndexNoCatalog(self):
        # Should not fail if portal_catalog is missing
        self.portal._delObject('portal_catalog')
        addGetObjPositionInParentIndex(self.portal, [])

    def testAddGetObjSizeMetadata(self):
        # Should add getObjSize to schema
        self.catalog.delColumn('getObjSize')
        addGetObjSizeMetadata(self.portal, [])
        self.failUnless('getObjSize' in self.catalog.schema())

    def testAddGetObjSizeMetadataTwice(self):
        # Should not fail if migrated again
        self.catalog.delColumn('getObjSize')
        addGetObjSizeMetadata(self.portal, [])
        addGetObjSizeMetadata(self.portal, [])
        self.failUnless('getObjSize' in self.catalog.schema())

    def testAddGetObjSizeMetadataNoCatalog(self):
        # Should not fail if catalog is missing
        self.portal._delObject('portal_catalog')
        addGetObjSizeMetadata(self.portal, [])

    def testUpdateNavTreeProperties(self):
        # Should add new navtree_properties
        self.removeNavTreeProperty('typesToList')
        self.removeNavTreeProperty('sortAttribute')
        self.removeNavTreeProperty('sortOrder')
        self.removeNavTreeProperty('sitemapDepth')
        self.removeNavTreeProperty('showAllParents')
        self.failIf(self.properties.navtree_properties.hasProperty('typesToList'))
        updateNavTreeProperties(self.portal, [])
        self.failUnless(self.properties.navtree_properties.hasProperty('typesToList'))
        self.failUnless(self.properties.navtree_properties.hasProperty('sortAttribute'))
        self.failUnless(self.properties.navtree_properties.hasProperty('sortOrder'))
        self.failUnless(self.properties.navtree_properties.hasProperty('sitemapDepth'))
        self.failUnless(self.properties.navtree_properties.hasProperty('showAllParents'))

    def testUpdateNavTreePropertiesTwice(self):
        # Should not fail if migrated again
        self.removeNavTreeProperty('typesToList')
        self.removeNavTreeProperty('sortAttribute')
        self.removeNavTreeProperty('sortOrder')
        self.removeNavTreeProperty('sitemapDepth')
        self.removeNavTreeProperty('showAllParents')
        self.failIf(self.properties.navtree_properties.hasProperty('typesToList'))
        updateNavTreeProperties(self.portal, [])
        updateNavTreeProperties(self.portal, [])
        self.failUnless(self.properties.navtree_properties.hasProperty('typesToList'))
        self.failUnless(self.properties.navtree_properties.hasProperty('sortAttribute'))
        self.failUnless(self.properties.navtree_properties.hasProperty('sortOrder'))
        self.failUnless(self.properties.navtree_properties.hasProperty('sitemapDepth'))
        self.failUnless(self.properties.navtree_properties.hasProperty('showAllParents'))

    def testUpdateNavTreePropertiesNoTool(self):
        # Should not fail if portal_properties is missing
        self.portal._delObject('portal_properties')
        updateNavTreeProperties(self.portal, [])

    def testUpdateNavTreePropertiesNoSheet(self):
        # Should not fail if navtree_properties is missing
        self.properties._delObject('navtree_properties')
        updateNavTreeProperties(self.portal, [])

    def testAddSitemapAction(self):
        # Should add the sitemap action
        self.removeActionFromTool('sitemap')
        self.failIf('sitemap' in [x.id for x in self.actions.listActions()])
        addSitemapAction(self.portal, [])
        self.failUnless('sitemap' in [x.id for x in self.actions.listActions()])

    def testAddSitemapActionTwice(self):
        # Should not fail if migrated again
        self.removeActionFromTool('sitemap')
        self.failIf('sitemap' in [x.id for x in self.actions.listActions()])
        addSitemapAction(self.portal, [])
        addSitemapAction(self.portal, [])
        self.failUnless('sitemap' in [x.id for x in self.actions.listActions()])

    def testAddSitemapActionNoTool(self):
        # Should not fail if portal_actions is missing
        self.portal._delObject('portal_actions')
        addSitemapAction(self.portal, [])

    def testReindexCatalog(self):
        # Should rebuild the catalog
        self.folder.invokeFactory('Document', id='doc', title='Foo')
        self.folder.doc.setTitle('Bar')
        self.assertEqual(len(self.catalog(Title='Foo')), 1)
        reindexCatalog(self.portal, [])
        self.assertEqual(len(self.catalog(Title='Foo')), 0)
        self.assertEqual(len(self.catalog(Title='Bar')), 1)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestMigrations_v2))
    suite.addTest(makeSuite(TestMigrations_v2_1))
    return suite

if __name__ == '__main__':
    framework()
