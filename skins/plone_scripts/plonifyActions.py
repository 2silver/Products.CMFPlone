## Script (Python) "plonifyActions"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=template_id, actions=None, default_tab='view'
##title=
##
here_url = context.absolute_url()
site_properties=context.portal_properties.site_properties

if actions is None:
    actions=context.portal_actions.listFilteredActionsFor()

actionlist=[]
if same_type(actions, {}):
    if context.getTypeInfo().getId() in site_properties.use_folder_tabs:
        actionlist=actions['folder']+actions['object']+actions.get('object_tabs',[])
    else:
        actionlist=actions['object']+actions.get('object_tabs',[])
   
plone_actions=[]
use_default=1
for action in actionlist:
    item={'name':'',
          'id':'',
          'url':'',
          'selected':''}

    item['name']=action['name']
    item['id']=actionid=action['id']

    aurl=action['url'].strip()
    if not aurl.startswith('http'):
        item['url']='%s/%s'%(here_url,aurl)
    else:
        item['url']=aurl

    if item['url'].split('/')[-1]==template_id:
        item['selected']=1
        use_default=0

    plone_actions.append(item)

if use_default:
    for action in plone_actions:
        if action['id']==default_tab:
            action['selected']=1
            break

return plone_actions 


