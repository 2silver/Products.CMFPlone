## Controller Python Script "reconfig"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=
##title=Reconfigure Portal

from Products.CMFPlone import PloneMessageFactory as _

REQUEST=context.REQUEST
portal_properties=context.portal_properties
portal_properties.editProperties(REQUEST)
portal_properties.site_properties.manage_changeProperties(REQUEST)
context.portal_url.getPortalObject().manage_changeProperties(REQUEST)

from Products.CMFPlone.utils import transaction_note
transaction_note('Reconfigured portal')

context.plone_utils.addPortalMessage(_(u'Portal reconfigured.'))
return state
