from Products.ExternalMethod.ExternalMethod import manage_addExternalMethod
from Products.CMFPlone.Portal import manage_addSite
from Products.SiteAccess.SiteRoot import manage_addSiteRoot
from Products.SiteAccess.AccessRule import manage_addAccessRule

from AccessControl import User
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from App.Extensions import getObject
from App.Common import package_home

import string
import glob 
import OFS.Application
import os
import sys
import zLOG

def create(app, admin_username='admin'):
    out = []
    oids = app.objectIds()

    # these are the two set elements...
    # (accessRule.py external method and SiteRoot)
    eid = 'accessRule.py'
    pid = 'Plone'
    emod = 'CMFPlone.accessRule'
    efn = 'accessRule'
    sid = 'SiteRoot'

    if pid in oids:
        out.append("A Plone site already exists")
        return out

    # 1 .get the admin user (dont bother making it, it's done before you
    #                        get a chance)

    acl_users = app.acl_users
#    info = User.readUserAccessFile('inituser')
#    if info:
#        acl_users._doAddUser(info[0], info[1], ('manage',), [])

    user = acl_users.getUser(admin_username)
    if user:
        user = user.__of__(acl_users)
        newSecurityManager(None, user)
        out.append("Retrieved the admin user")
    else:
        out.append("Retrieving admin user failed")

    # 2. create the access rule external method
    if eid not in oids:
        # this is the actual access rule
        manage_addExternalMethod(app, 
                                 eid, 
                                 'Plone Access Rule', 
                                 emod, 
                                 efn)
        out.append("Added external method")
        # this sets the access rule
        manage_addAccessRule(app, eid)
        out.append("Set an access rule")
##         if user:
##             getattr(app, eid).changeOwnership(user)

    # 3. actually add in Plone
    if pid not in oids:
        manage_addSite(app, 
                   pid, 
                   title='Portal', 
                   description='',
                   create_userfolder=1,
                   email_from_address='postmaster@localhost',
                   email_from_name='Portal Administrator',
                   validate_email=0,
                   custom_policy='Default Plone',
                   RESPONSE=None)
        out.append("Added Plone")
##         if user:
##             getattr(app, pid).changeOwnership(user, recursive=1)

    # 4. adding the site root in
    plone = getattr(app, pid)
    if sid not in plone.objectIds():
        manage_addSiteRoot(plone)
        out.append("Added Site Root")
##         if user:
##             getattr(plone, sid).changeOwnership(user)
  
    # 5. add in products
    qit = plone.portal_quickinstaller
    
    ids = [ x['id'] for x in qit.listInstallableProducts(skipInstalled=1) ]
    qit.installProducts(ids)
    
    # 6. commit
    get_transaction().commit()

    noSecurityManager()
    out.append("Finished")
    return out
