from __future__ import nested_scopes
import new

import os
import urllib
import Globals
from AccessControl import Owned, ClassSecurityInfo, getSecurityManager
from Acquisition import aq_parent, aq_base, aq_inner, aq_get
from OFS.SimpleItem import SimpleItem
from ZPublisher.Publish import call_object, missing_name, dont_publish_class
from ZPublisher.mapply import mapply
from Products.CMFPlone import cmfplone_globals
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.CMFCore import CMFCorePermissions
from Products.CMFCore.utils import UniqueObject, getToolByName, format_stx
from Products.CMFPlone.PloneFolder import PloneFolder as TempFolderBase
from Products.CMFPlone.PloneBaseTool import PloneBaseTool



# Use the following to patch a single class instance (courtesy of 
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66543)
# Do not try this at home.  I mean it.
def patch_instance_method(klass, method_name, new_method):
    old_method = getattr(klass, method_name)
    # bind the old method to the new
    bound_new_method = lambda *args, **kwds: new_method(old_method, *args, **kwds)
    # now patch the instance
    setattr(klass, method_name, new.instancemethod(bound_new_method, klass, klass.__class__))

# patched version of __ac_local_roles__ used for portal_factory created objects
# We need the patch because the object is created during traversal, when the
# currently authenticated user is unknown, so the owner is not set correctly.
def patched__ac_local_roles__(__ac_local_roles__, self):
    member = getToolByName(self, 'portal_membership').getAuthenticatedMember()
    username = member.getUserName()
    # try to get original __ac_local_roles__
    local_roles = __ac_local_roles__
    if callable(local_roles):
        local_roles = local_roles(self)
    local_roles = local_roles or {}
    # amend original local roles (if any)
    if not local_roles.has_key(username):
        local_roles[username] = []
    if not 'Owner' in local_roles[username]:
        local_roles[username].append('Owner')
    return local_roles


# ##############################################################################
# A class used for generating the temporary folder that will
# hold temporary objects.  We need a separate class so that
# we can add all types to types_tool's allowed_content_types
# for the class without having side effects in the rest of
# the portal.
class TempFolder(TempFolderBase):
    portal_type = meta_type = 'TempFolder'
    isPrincipiaFolderish = 0

    # override getPhysicalPath so that temporary objects return a full path
    # that includes the acquisition parent of portal_factory (otherwise we get
    # portal_root/portal_factory/... no matter where the object will reside)
    def getPhysicalPath(self):
        '''Returns a path (an immutable sequence of strings)
        that can be used to access this object again
        later, for example in a copy/paste operation.  getPhysicalRoot()
        and getPhysicalPath() are designed to operate together.
        '''
        portal_factory = aq_parent(aq_inner(self))
        path = aq_parent(portal_factory).getPhysicalPath() + (portal_factory.getId(), self.getId(),)

        return path

    # override / delegate local roles methods
    def __ac_local_roles__(self):
        """__ac_local_roles__ needs to be handled carefully.
        Zope's and GRUF's User.getRolesInContext both walk up the
        acquisition hierarchy using aq_parent(aq_inner(obj)) when
        they gather local roles, and this process will result in
        their walking from TempFolder to portal_factory to the portal root.
        XXX If we implement PLIP16, this will have to be modified!!!"""
        object = aq_parent(aq_parent(self))
        local_roles = {}
        while 1:
            # Get local roles for this user
            lr = getattr(object, '__ac_local_roles__', None)
            if lr:
                if callable(lr):
                    lr=lr()
                lr = lr or {}
                for k, v in lr.items():
                    if not local_roles.has_key(k):
                        local_roles[k] = []
                    for role in v:
                        if not role in local_roles[k]:
                            local_roles[k].append(role)

            # Prepare next iteration
            inner = getattr(object, 'aq_inner', object)
            parent = getattr(inner, 'aq_parent', None)
            if parent is not None:
                object = parent
                continue
            if hasattr(object, 'im_self'):
                object=object.im_self
                object=getattr(object, 'aq_inner', object)
                continue
            break
        return local_roles

    def has_local_roles(self):
        return len(self.__ac_local_roles__())

    def get_local_roles_for_userid(self, userid):
        return tuple(self.__ac_local_roles__().get(userid, []))

    def get_valid_userids(self):
        return aq_parent(aq_parent(self)).get_valid_userids()

    def valid_roles(self):
        return aq_parent(aq_parent(self)).valid_roles()

    def validate_roles(self, roles):
        return aq_parent(aq_parent(self)).validate_roles(roles)

    def userdefined_roles(self):
        return aq_parent(aq_parent(self)).userdefined_roles()

    # delegate Owned methods
    def owner_info(self):
        return aq_parent(aq_parent(self)).owner_info()

    def getOwner(self, info=0,
                 aq_get=aq_get,
                 UnownableOwner=Owned.UnownableOwner,
                 getSecurityManager=getSecurityManager,
                 ):
        return aq_parent(aq_parent(self)).getOwner(info, aq_get, UnownableOwner, getSecurityManager)

    def userCanTakeOwnership(self):
        return aq_parent(aq_parent(self)).userCanTakeOwnership()

    # delegate allowedContentTypes
    def allowedContentTypes(self):
        return aq_parent(aq_parent(self)).allowedContentTypes()

    # override __getitem__
    def __getitem__(self, id):
        # Zope's inner acquisition chain for objects returned by __getitem__ will be
        # portal -> portal_factory -> temporary_folder -> object
        # What we really want is for the inner acquisition chain to be
        # intended_parent_folder -> portal_factory -> temporary_folder -> object
        # So we need to rewrap...
        portal_factory = aq_parent(self)
        intended_parent = aq_parent(portal_factory)

        # If the intended parent has an object with the given id, just do a passthrough
        if hasattr(intended_parent, id):
            return getattr(intended_parent, id)

        # rewrap portal_factory
        portal_factory = aq_base(portal_factory).__of__(intended_parent)
        # rewrap self
        temp_folder = aq_base(self).__of__(portal_factory)

        if id in self.objectIds():
            return (aq_base(self._getOb(id)).__of__(temp_folder)).__of__(intended_parent)
        else:
            type_name = self.getId()
            try:
                self.invokeFactory(id=id, type_name=type_name)
            except:
                # some errors from invokeFactory (AttributeError, maybe others) 
                # get swallowed -- dump the exception to the log to make sure
                # developers can see what's going on
                getToolByName(self, 'plone_utils').logException()
                raise
            obj = self._getOb(id)
            obj.unindexObject()  # keep obj out of the catalog

            # patch object's __ac_local_roles__ method (see above)
            patch_instance_method(obj, '__ac_local_roles__', patched__ac_local_roles__)
            return (aq_base(obj).__of__(temp_folder)).__of__(intended_parent)

    # ignore rename requests since they don't do anything
    def manage_renameObject(self, id1, id2):
        pass



# ##############################################################################
class FactoryTool(PloneBaseTool, UniqueObject, SimpleItem):
    """ """
    id = 'portal_factory'
    meta_type= 'Plone Factory Tool'
    toolicon = 'skins/plone_images/add_icon.gif'
    security = ClassSecurityInfo()
    isPrincipiaFolderish = 0
    
    __implements__ = (PloneBaseTool.__implements__, SimpleItem.__implements__, )

    manage_options = ( ({'label':'Overview', 'action':'manage_overview'}, \
                        {'label':'Documentation', 'action':'manage_docs'}, \
                        {'label':'Factory Types', 'action':'manage_portal_factory_types'},) +
                       SimpleItem.manage_options)

    security.declareProtected(CMFCorePermissions.ManagePortal, 'manage_overview')
    manage_overview = PageTemplateFile('www/portal_factory_manage_overview', globals())
    manage_overview.__name__ = 'manage_overview'
    manage_overview._need__name__ = 0

    security.declareProtected(CMFCorePermissions.ManagePortal, 'manage_portal_factory_types')
    manage_portal_factory_types = PageTemplateFile(os.path.join('www', 'portal_factory_manage_types'), globals())
    manage_portal_factory_types.__name__ = 'manage_portal_factory_types'
    manage_portal_factory_types._need__name__ = 0

    manage_main = manage_overview

    security.declareProtected(CMFCorePermissions.ManagePortal, 'manage_docs')
    manage_docs = PageTemplateFile(os.path.join('www','portal_factory_manage_docs'), globals())
    manage_docs.__name__ = 'manage_docs'

    wwwpath = os.path.join(Globals.package_home(cmfplone_globals), 'www')
    f = open(os.path.join(wwwpath, 'portal_factory_docs.stx'), 'r')
    _docs = f.read()
    f.close()
    _docs = format_stx(_docs)

    security.declarePublic('docs')
    def docs(self):
        """Returns FactoryTool docs formatted as HTML"""
        return self._docs


    def getFactoryTypes(self):
        if not hasattr(self, '_factory_types'):
            self._factory_types = {}
        return self._factory_types


    security.declareProtected(CMFCorePermissions.ManagePortal, 'manage_setPortalFactoryTypes')
    def manage_setPortalFactoryTypes(self, REQUEST=None, listOfTypeIds=None):
        """Set the portal types that should use the factory."""
        if listOfTypeIds is not None:
            dict = {}
            for l in listOfTypeIds:
                dict[l] = 1
        elif REQUEST is not None:
            dict = REQUEST.form
        if dict is None:
            dict = {}
        self._factory_types = {}
        types_tool = getToolByName(self, 'portal_types')
        for t in types_tool.listContentTypes():
            if dict.has_key(t):
                self._factory_types[t] = 1
        self._p_changed = 1
        if REQUEST:
            REQUEST.RESPONSE.redirect('manage_main')


    def doCreate(self, obj, id=None, **kw):
        """Create a real object from a temporary object."""
        if not self.isTemporary(obj=obj):
            return obj
        else:
            if id is not None:
                id = id.strip()
            if hasattr(obj, 'getId') and callable(getattr(obj, 'getId')):
                obj_id = obj.getId()
            else:
                obj_id = getattr(obj, 'id', None)
            if obj_id is None:
                raise Exception  # XXX - FIXME
            if not id:
                id = obj_id
            type_name = aq_parent(aq_inner(obj)).id
            folder = aq_parent(aq_parent(aq_parent(aq_inner(obj))))
            folder.invokeFactory(id=id, type_name=type_name)
            obj = getattr(folder, id)

            # give ownership to currently authenticated member if not anonymous
            membership_tool = getToolByName(self, 'portal_membership')
            if not membership_tool.isAnonymousUser():
                member = membership_tool.getAuthenticatedMember()
                obj.changeOwnership(member.getUser(), 1)
                obj.manage_setLocalRoles(member.getUserName(), ['Owner'])

            return obj


    def isTemporary(self, obj):
        """Check to see if an object is temporary"""
        ob = aq_parent(aq_inner(obj))
        return hasattr(ob, 'meta_type') and ob.meta_type == TempFolder.meta_type


#    index_html = None  # call __call__, not index_html


    def getTempFolder(self, type_name):
        factory_info = self.REQUEST.get('__factory_info__', {})
        tempFolder = factory_info.get(type_name, None)
        if not tempFolder:
            type_name = urllib.unquote(type_name)
            # make sure we can add an object of this type to the temp folder
            types_tool = getToolByName(self, 'portal_types')
            if not type_name in types_tool.listContentTypes():
                raise ValueError, 'Unrecognized type %s\n' % type_name
            if not type_name in types_tool.TempFolder.allowed_content_types:
                # update allowed types for tempfolder
                types_tool.TempFolder.allowed_content_types=(types_tool.listContentTypes())

            tempFolder = TempFolder(type_name)
            tempFolder.parent = aq_parent(self)
            tempFolder = aq_inner(tempFolder).__of__(self)
            tempFolder.manage_permission(CMFCorePermissions.AddPortalContent, ('Anonymous','Authenticated',), acquire=0 )
            tempFolder.manage_permission(CMFCorePermissions.ModifyPortalContent, ('Anonymous','Authenticated',), acquire=0 )
            tempFolder.manage_permission('Copy or Move', ('Anonymous','Authenticated',), acquire=0 )
        else:
            tempFolder = aq_inner(tempFolder).__of__(self)
        factory_info[type_name] = tempFolder
        self.REQUEST.set('__factory_info__', factory_info)

        return tempFolder


    def __bobo_traverse__(self, REQUEST, name):
        """ """
        # The portal factory intercepts URLs of the form
        #   .../portal_factory/TYPE_NAME/ID/...
        # where TYPE_NAME is a type from portal_types.listContentTypes() and
        # ID is the desired ID for the object.  For intercepted URLs,
        # portal_factory creates a temporary object of type TYPE_NAME with
        # id ID and puts it on the traversal stack.  The context for the
        # temporary object is set to portal_factory's context.
        #
        # If the object with id ID already exists in portal_factory's context,
        # portal_factory returns the existing object.
        #
        # All other requests are passed through unchanged.
        #

        # try to extract a type string from next piece of the URL

        # unmangle type name
        type_name = urllib.unquote(name)
        types_tool = getToolByName(self, 'portal_types')
        # make sure this is really a type name
        if not type_name in types_tool.listContentTypes():
            # nope -- do nothing
            return getattr(self, name)
        return self.getTempFolder(name)

Globals.InitializeClass(FactoryTool)
