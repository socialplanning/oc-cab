from Products.CMFCore.utils import getToolByName
from opencore.cabochon.interfaces import ICabochonClient
from opencore.interfaces import IProject
from zope.app.container.contained import IObjectRemovedEvent
from zope.component import adapter

@adapter(IProject, IObjectRemovedEvent)
def notify_cabochon(project, event=None):
    # project info passed to cabochon
    id = project.getId()

    # FIXME for some reason, on test tear down the getUtility fails
    # without explicitly passing a context
    portal = getToolByName(project, 'portal_url').getPortalObject()
    cabochon_utility = getUtility(ICabochonClient, context=portal)
    cabochon_utility.notify_project_deleted(id)
