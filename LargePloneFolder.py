from Acquisition import aq_base, aq_inner
from ComputedAttribute import ComputedAttribute
from Globals import InitializeClass
from PloneFolder import BasePloneFolder, ReplaceableWrapper
from PloneFolder import factory_type_information as PloneFolder_fti
from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2Base

# Pure laziness
factory_type_information={}
factory_type_information.update(PloneFolder_fti)
factory_type_information.update( {'id':'Large Plone Folder',
                                  'meta_type':'Large Plone Folder',
                                  'factory':'addLargePloneFolder',
                                  'global_allow':0} )

class LargePloneFolder(BTreeFolder2Base, BasePloneFolder):
    meta_type='Large Plone Folder'

    # BTreeFolder2Base has no __implements__
    __implements__ = BasePloneFolder.__implements__
    

    def __init__(self, id, title=''):
        BTreeFolder2Base.__init__(self, id)
        BasePloneFolder.__init__(self, id, title)
        self.id=id
        self.title=title

    # as per CMFBTreeFolder.py
    def _checkId(self, id, allow_dup=0):
        BasePloneFolder._checkId(self, id, allow_dup)
        BTreeFolder2Base._checkId(self, id, allow_dup)

    manage_renameObject = BasePloneFolder.inheritedAttribute('manage_renameObject')

    # this works around a problem that makes empty folders
    # evaluate to false in boolean tests, like:
    # tal:condition="python: someFolder and someFolder.someMethod(...)"
    __len__ = BasePloneFolder.__len__


    def index_html(self):
        """ 
        btree folders don't store objects as attributes, the implementation of index_html
        method in plone folder assumes this and by virtue of its being invoked looked in
        the parent container. we override here to check the btree data structs, and then
        perform the same lookup as BasePloneFolder if we don't find it.       
        """
        _target = self.get('index_html')
        if _target is not None:
            return _target
        _target = aq_parent(aq_inner(self)).aq_acquire('index_html')
        return ReplaceableWrapper(aq_base(_target).__of__(self))

    index_html = ComputedAttribute(index_html)

InitializeClass(LargePloneFolder)

def addLargePloneFolder(self, id, title='', description='', REQUEST=None):
    """ add a BTree-backed Plone Folder """
    obj = LargePloneFolder(id, title=title)
    obj.setDescription(description)
    self._setObject(id, obj)
    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect( sf.absolute_url() + '/manage_main' )

