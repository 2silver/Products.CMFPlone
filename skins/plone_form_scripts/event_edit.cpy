## Controller Python Script "event_edit"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=title=None, description=None, event_type=None, start_date=None, end_date=None, location=None, contact_name=None, contact_email=None, contact_phone=None, event_url=None, id='' 
##title=Edit an event
##

# if there is no id specified, keep the current one
if not id:
    id = context.getId()

# need to parse date string *before* passing to Event.edit since
# it expects bite sized chunks....
from DateTime import DateTime

dt_start = DateTime(start_date)
dt_end = DateTime(end_date)

try:
    new_context = context.portal_factory.doCreate(context, id)
    new_context.edit( title=title
                    , description=description
                    , eventType=event_type
                    , effectiveYear=dt_start.year()
                    , effectiveMo=dt_start.month()
                    , effectiveDay=dt_start.day()
                    , expirationYear=dt_end.year()
                    , expirationMo=dt_end.month()
                    , expirationDay=dt_end.day()
                    , start_time='%2.2d:%2.2d'%(dt_start.h_24(), dt_start.minute())
                    , startAMPM=dt_start.ampm()
                    , stopAMPM=dt_end.ampm()
                    , stop_time='%2.2d:%2.2d'%(dt_end.h_24(), dt_end.minute())
                    , location=location
                    , contact_name=contact_name
                    , contact_email=contact_email
                    , contact_phone=contact_phone
                    , event_url=event_url )

    new_context.plone_utils.contentEdit( new_context
                                       , id=id
                                       , description=description )
except: #XXX DateTime and contentEdit() has many things that could go wrong - catch all.
    return state.set(portal_status_message='Error saving event.', new_status='failure')

return state.set(context=new_context, portal_status_message='Event changes saved.')
