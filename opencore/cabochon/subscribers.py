from DateTime import DateTime
from opencore.cabochon.interfaces import ICabochonClient
from opencore.interfaces import IOpenPage, IProject
from opencore.project.browser.projectinfo import ProjectInfo
from Products.CMFCore.utils import getToolByName
from zope.app.container.contained import IObjectRemovedEvent, IObjectAddedEvent
from zope.app.event.interfaces import IObjectModifiedEvent
from zope.component import adapter
from zope.component import getUtility


@adapter(IProject, IObjectRemovedEvent)
def notify_project_deleted(project, event=None):
    # project info passed to cabochon
    id = project.getId()

    cabochon_utility = getUtility(ICabochonClient)
    cabochon_utility.notify_project_deleted(id)



@adapter(IOpenPage, IObjectAddedEvent)
def notify_wikipage_created(page, event=None):
    parent = event.newParent
    if not IProject.providedBy(parent):
        return #notify only on projects for now

    page_url = page.absolute_url()

    mtool = getToolByName(page, 'portal_membership')
    member = mtool.getAuthenticatedMember()
    username = member.getId()
    cabochon_utility = getUtility(ICabochonClient)
    cabochon_utility.notify_wikipage_created(parent, page.title_or_id(), page_url, username)

@adapter(IOpenPage, IObjectRemovedEvent)
def notify_wikipage_deleted(page, event=None):
    parent = event.oldParent
    if not IProject.providedBy(parent):
        return #notify only on projects for now

    page_url = page.absolute_url()

    mtool = getToolByName(page, 'portal_membership')
    member = mtool.getAuthenticatedMember()
    username = member.getId()
    cabochon_utility = getUtility(ICabochonClient)
    cabochon_utility.notify_wikipage_deleted(page_url, username)


@adapter(IOpenPage, IObjectModifiedEvent)
def notify_wikipage_modified(page, event=None):
    #this is also fired shortly after the event is created, for some rason.
    if (DateTime() - page.created()) * 100000 < 5:
        return #page too new; was probably the on-create modified event

    parent = ProjectInfo(page).project
    if not parent:
        return

    page_url = page.absolute_url()

    mtool = getToolByName(page, 'portal_membership')
    member = mtool.getAuthenticatedMember()
    username = member.getId()
    cabochon_utility = getUtility(ICabochonClient)
    cabochon_utility.notify_wikipage_updated(parent, page.title_or_id(), page_url, username)
