## Controller Python Script "folder_rename"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=paths=[],new_ids=[],new_titles=[]
##title=Rename Objects
##

from Products.CMFPlone.utils import transaction_note
from Products.CMFPlone import PloneMessageFactory as _
from ZODB.POSException import ConflictError

portal = context.portal_url.getPortalObject()
failed = {}
success = {}

request = context.REQUEST

message = None

for x in range(0, len(new_ids)):
    new_id = new_ids[x]
    path = paths[x]
    new_title = new_titles[x]
    obj = portal.restrictedTraverse(path)
    id = obj.getId()
    title = obj.Title()
    try:
        if new_title and title != new_title:
            obj.setTitle(new_title)
            success[path]=(new_id,new_title)
        if new_id and id != new_id:
            origPath = '/'.join(obj.getPhysicalPath())
            parent = obj.aq_inner.aq_parent
            parent.manage_renameObjects((id,), (new_id,))
            success[path]=(new_id,new_title)
            orig_template = request.get('orig_template', None)
            real_orig = orig_template
            if orig_template is not None and orig_template == origPath:
                newObj = parent[new_id]
                orig_template = '/'.join(newObj.getPhysicalPath())
                request.set('orig_template', orig_template)
                message = "Renamed '%s' to '%s'" % (id, new_id)
        else:
            obj.reindexObject()
    except ConflictError:
        raise
    except Exception,e:
        failed[path]=e

message = _(u'${count} item(s) renamed.', mapping={u'count' : str(len(success))})
if failed:
    message = _(u'The following item(s) could not be renamed: ${items}.', 
                mapping={u'items' : ', '.join(failed.keys())})
transaction_note('Renamed %s' % str(success.keys))

context.plone_utils.addPortalMessage(message)
return state
