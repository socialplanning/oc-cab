from opencore.cabochon.interfaces import ICabochonClient
from opencore.interfaces import IProject
from zope.app.container.contained import IObjectRemovedEvent
from zope.component import adapter
from zope.component import getUtility

@adapter(IProject, IObjectRemovedEvent)
def notify_project_deleted(project, event=None):
    # project info passed to cabochon
    id = project.getId()

    cabochon_utility = getUtility(ICabochonClient)
    cabochon_utility.notify_project_deleted(id)
