from Globals import InitializeClass, DTMLFile, package_home
from Acquisition import aq_base, aq_inner, aq_parent
from AccessControl import ClassSecurityInfo
from OFS.Folder import Folder
from OFS.SimpleItem import SimpleItem
from OFS.PropertyManager import PropertyManager

from Products.CMFCore.Expression import Expression, createExprContext
from Products.CMFCore.ActionInformation import ActionInformation, oai
from Products.CMFCore.ActionProviderBase import ActionProviderBase
from Products.CMFCore.TypesTool import TypeInformation
from Products.CMFCore.CMFCorePermissions import ManagePortal, SetOwnProperties, SetOwnPassword, View
from Products.CMFCore.utils import _checkPermission, _dtmldir, getToolByName, SimpleItemWithProperties, UniqueObject

from Products.CMFCore.interfaces.portal_actions import portal_actions as IActionsTool

import ToolNames
from interfaces.PloneControlPanel import IControlPanel

class PloneConfiglet(ActionInformation):
    def __init__(self,appId,**kwargs):
        self.appId=appId
        ActionInformation.__init__(self,**kwargs)

    def getAppId(self):
        return self.appId

    def getDescription(self):
        return self.description

    def clone(self):
        return self.__class__(**self.__dict__)

    def getAction(self,ec):
        res=ActionInformation.getAction(self,ec)
        res['description']=self.getDescription()
        return res

default_configlets = (
    {'id':'QuickInstaller',
     'appId':'QuickInstaller',
     'name':'Add/Remove Products',
     'action':'string:${portal_url}/prefs_install_products_form',
     'category':'Plone',
     'permission': ManagePortal,
     'imageUrl':'product_icon.gif'},

    {'id':'PloneReconfig',
     'appId':'Plone',
     'name':'Portal Settings',
     'action':'string:${portal_url}/reconfig_form',
     'category':'Plone',
     'permission': ManagePortal,
     'imageUrl':'logoIcon.gif'},

    {'id':'UsersGroups',
     'appId':'UsersGroups',
     'name':'Users and Groups Administration',
     'action':'string:${portal_url}/prefs_users_overview',
     'category':'Plone',
     'permission': ManagePortal,
     'imageUrl':'group.gif'},

    {'id':'UsersGroups2',
     'appId':'UsersGroups',
     'name':'Users and Groups Administration',
     'action':'string:${portal_url}/prefs_groups_overview',
     'category':'Plone',
     'permission': ManagePortal,
     'visible' : 0,
     'imageUrl':'group.gif'},

    {'id':'MemberPrefs',
     'appId':'Plone',
     'name':'Personal Preferences',
     'action':'string:${portal_url}/personalize_form',
     'category':'Member',
     'permission': SetOwnProperties,
     'imageUrl':'user.gif'},

    {'id':'MemberPassword',
     'appId':'Plone',
     'name':'Change Password',
     'action':'string:${portal_url}/password_form',
     'category':'Member',
     'permission': SetOwnPassword,
     'imageUrl':'lock_icon.gif'},

#    {'id':'WorkflowPrefs',
#     'appId':'Plone',
#     'name':'Manage Workflow',
#     'action':'string:${portal_url}/prefs_workflow_basic',
#     'category':'Plone',
#     'permission': ManagePortal,
#     'imageUrl':'site_icon.gif'},

    {'id':'MailHost',
     'appId':'MailHost',
     'name':'Mail Settings',
     'action':'string:${portal_url}/prefs_mailhost_form',
     'category':'Plone',
     'permission': ManagePortal,
     'imageUrl':'mail_icon.gif'},

    {'id':'PortalSkin',
     'appId':'PortalSkin',
     'name':'Skins',
     'action':'string:${portal_url}/prefs_portalskin_form',
     'category':'Plone',
     'permission': ManagePortal,
     'imageUrl':'skins_icon.gif'},

#    {'id':'Syndication',
#     'appId':'Syndication',
#     'name':'Syndication',
#     'action':'string:${portal_url}/prefs_syndication_form',
#     'category':'Plone',
#     'permission': ManagePortal,
#     'imageUrl':'site_icon.gif'},

    {'id':'errorLog',
     'appId':'ErrorLog',
     'name':'Error Log',
     'action':'string:${portal_url}/prefs_error_log_form',
     'category':'Plone',
     'permission': ManagePortal,
     'imageUrl':'error_log_icon.gif'},

#   {'id':'PortalProperties',
#     'appId':'PortalProperties',
#     'name':'PortalProperties',
#     'action':'string:${portal_url}/prefs_portal_properties_list',
#     'category':'Plone',
#     'permission': ManagePortal,
#     'imageUrl':'site_icon.gif'},

    {
        'id':'ZMI',
        'appId':'ZMI',
        'name':'Zope Management Interface',
        'action':'string:${portal_url}/manage_main',
        'category':'Plone',
     'permission': ManagePortal,
     'imageUrl':'zope_icon.gif'},


)



class PloneControlPanel(UniqueObject, Folder, ActionProviderBase, PropertyManager):
    """
        Weave together the various sources of "actions" which are apropos
        to the current user and context.
    """

    __implements__ = (IControlPanel, ActionProviderBase.__implements__)

    security = ClassSecurityInfo()

    id = 'portal_controlpanel'
    title = 'Control Panel'
    toolicon = 'skins/plone_images/site_icon.gif'
    meta_type = ToolNames.ControlPanelTool
    _actions_form = DTMLFile( 'www/editPloneConfiglets', globals() )

    _properties=(
        {'id':'groups','type':'lines'},
    )

    manage_options=ActionProviderBase.manage_options + PropertyManager.manage_options

    groups=['site|Plone|Plone Configuration','site|Products|Add-on Product Configuration','member|Member|Plone Member Preferences']

    def __init__(self,**kw):
        if kw:
            self.__dict__.update(**kw)

    security.declareProtected( ManagePortal, 'registerConfiglets' )
    def registerConfiglets(self,configlets):
        ''' attention: must be called AFTER portal_actionicons is installed '''
        for conf in configlets:
            self.registerConfiglet(**conf)

    security.declareProtected( ManagePortal, 'registerDefaultConfiglets' )
    def registerDefaultConfiglets(self):
        """ We need to bootstrap the default_configlets into the control panel """
        self.registerConfiglets(default_configlets)

    security.declareProtected( ManagePortal, 'getGroupIds' )
    def getGroupIds(self,category=''):
        return [g.split('|')[1] for g in self.groups if category=='' or g.split('|')[0]==category]

    security.declareProtected( View, 'getGroups' )
    def getGroups(self,category=''):
        return [{'id':g.split('|')[1],'title':g.split('|')[2]} for g in self.groups if category=='' or g.split('|')[0]==category]

    security.declareProtected( SetOwnProperties, 'enumConfiglets' )
    def enumConfiglets(self,group=None):
        portal=getToolByName(self,'portal_url').getPortalObject()
        context=createExprContext(self,portal,self)
        res = [a.getAction(context) for a in self.listActions() if a.category==group and a.testCondition(context)]
        res.sort(lambda a,b:cmp(a['name'],b['name']))
        return res

    security.declareProtected( ManagePortal, 'unregisterConfiglet' )
    def unregisterConfiglet(self,id):
        actids= [o.id for o in self.listActions()]
        selection=[actids.index(a) for a in actids if a==id]
        self.deleteActions(selection)

        actionicons=getToolByName(self,'portal_actionicons')
        if actionicons.queryActionInfo('controlpanel', id, None):
            actionicons.removeActionIcon('controlpanel', id)


    security.declareProtected( ManagePortal, 'unregisterApplication' )
    def unregisterApplication(self,appId):
        acts=list(self.listActions())
        selection=[acts.index(a) for a in acts if a.appId==appId]
        self.deleteActions(selection)

        actionicons=getToolByName(self,'portal_actionicons')
        for a in acts:
            if a.appId == appId and actionicons.queryActionInfo('controlpanel', a.id, None):
                actionicons.removeActionIcon('controlpanel', a.id)



    def _extractAction( self, properties, index ):

        """ Extract an ActionInformation from the funky form properties.
        """
        id          = str( properties.get( 'id_%d'          % index, '' ) )
        name        = str( properties.get( 'name_%d'        % index, '' ) )
        action      = str( properties.get( 'action_%d'      % index, '' ) )
        condition   = str( properties.get( 'condition_%d'   % index, '' ) )
        category    = str( properties.get( 'category_%d'    % index, '' ))
        visible     =      properties.get( 'visible_%d'     % index, 0  )
        permissions =      properties.get( 'permission_%d'  % index, () )
        appId       =      properties.get( 'appId_%d'  % index, '' )
        description =      properties.get( 'description_%d'  % index, '' )

        if not name:
            raise ValueError('A name is required.')

        if action is not '':
            action = Expression( text=action )

        if condition is not '':
            condition = Expression( text=condition )

        if category == '':
            category = 'object'

        if type( visible ) is not type( 0 ):
            try:
                visible = int( visible )
            except ValueError:
                visible = 0

        if type( permissions ) is type( '' ):
            permissions = ( permissions, )

        return PloneConfiglet( id=id
                                , title=name
                                , action=action
                                , condition=condition
                                , permissions=permissions
                                , category=category
                                , visible=visible
                                , appId = appId
                                , description = description
                                )
    security.declareProtected( ManagePortal, 'addAction' )
    def addAction( self
                 , id
                 , name
                 , action
                 , condition=''
                 , permission=''
                 , category='Plone'
                 , visible=1
                 , appId=None
                 , imageUrl=None
                 , description=''
                 , REQUEST=None
                 ):
        """ Add an action to our list.
            attention: must be called AFTER portal_actionicons is installed

        """
        if not name:
            raise ValueError('A name is required.')

        a_expr = action and Expression(text=str(action)) or ''
        c_expr = condition and Expression(text=str(condition)) or ''

        if type( permission ) != type( () ):
            permission = permission and (str(permission),) or ()

        new_actions = self._cloneActions()

        new_action = PloneConfiglet( id=str(id)
                                      , title=str(name)
                                      , action=a_expr
                                      , condition=c_expr
                                      , permissions=permission
                                      , category=str(category)
                                      , visible=int(visible)
                                      , appId=appId
                                      , description=description
                                      )

        new_actions.append( new_action )
        self._actions = tuple( new_actions )

        if imageUrl:
            actionicons=getToolByName(self,'portal_actionicons')
            actionicons.addActionIcon('controlpanel',new_action.id,imageUrl,new_action.title)


        if REQUEST is not None:
            return self.manage_editActionsForm(
                REQUEST, manage_tabs_message='Added.')

    registerConfiglet=addAction

    security.declareProtected( ManagePortal, 'manage_editActionsForm' )
    def manage_editActionsForm( self, REQUEST, manage_tabs_message=None ):

        """ Show the 'Actions' management tab.
        """
        actions = []

        for a in self.listActions():

            a1 = {}
            a1['id'] = a.getId()
            a1['name'] = a.Title()
            p = a.getPermissions()
            if p:
                a1['permission'] = p[0]
            else:
                a1['permission'] = ''
            a1['category'] = a.getCategory() or 'object'
            a1['visible'] = a.getVisibility()
            a1['action'] = a.getActionExpression()
            a1['condition'] = a.getCondition()
            a1['appId'] = a.getAppId()
            a1['description']=a.getDescription()
            actions.append(a1)

        # possible_permissions is in AccessControl.Role.RoleManager.
        pp = self.possible_permissions()
        return self._actions_form( self
                                 , REQUEST
                                 , actions=actions
                                 , possible_permissions=pp
                                 , management_view='Actions'
                                 , manage_tabs_message=manage_tabs_message
                                 )
