from cabochonclient import datetime_to_string
from datetime import datetime
from opencore.cabochon.interfaces import ICabochonClient
from opencore.interfaces import IOpenPage, IProject
from opencore.project.browser.projectinfo import ProjectInfo
from Products.CMFCore.utils import getToolByName
from zope.app.container.contained import IObjectRemovedEvent
from zope.app.container.contained import IObjectAddedEvent
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
    # mark the request object so we don't fire more than one event per
    # request; sucks to use acquisition here, but we don't have a
    # get_request function yet
    request = page.REQUEST
    if getattr(request, '_cab_already_notified', False):
        return
    request._cab_already_notified = True
    parent = event.newParent
    url = page.absolute_url()
    mtool = getToolByName(page, 'portal_membership')
    member = mtool.getAuthenticatedMember()
    username = member.getId()
    title = page.title_or_id()
    updated = datetime_to_string(datetime.now())
    object_type = 'page'
    action = 'created'
    project = ProjectInfo(page).project
    closed = 0
    categories = ['wiki']

    feed_kwargs = dict(link=url)
    if project is not None:
        proj_id = project.getId()
        feed_kwargs['project'] = proj_id
        categories.append('projects/%s' % proj_id)
        wfp = project._getOb('.wf_policy_config', None)
        if wfp is not None:
            policy = wfp.getPolicyIn().getId()
            if policy.startswith('closed'):
                closed = 1

    feed_kwargs['closed'] = closed
    feed_kwargs['categories'] = categories

    cabochon_utility = getUtility(ICabochonClient)
    cabochon_utility.send_feed_item(page.getId(), object_type, action, title,
                                    updated, username, **feed_kwargs)

    # XXX older-style notifier, can we refactor these so we don't have so
    # many methods?
    cabochon_utility.notify_wikipage_created(parent, title, url, username)

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
    # mark the request object so we don't fire more than one event per
    # request; sucks to use acquisition here, but we don't have a
    # get_request function yet
    request = page.REQUEST
    if getattr(request, '_cab_already_notified', False):
        return
    request._cab_already_notified = True

    project = ProjectInfo(page).project
    url = page.absolute_url()
    mtool = getToolByName(page, 'portal_membership')
    member = mtool.getAuthenticatedMember()
    username = member.getId()
    title = page.title_or_id()
    updated = datetime_to_string(datetime.now())
    object_type = 'page'
    action = 'modified'
    closed = 0
    categories = ['wiki']
    summary = "Wiki page '%s' edited" % title

    feed_kwargs = dict(link=url)
    if project is not None:
        proj_id = project.getId()
        feed_kwargs['project'] = proj_id
        categories.append('projects/%s' % proj_id)
        summary += " (in project '%s')" % project.title_or_id()
        wfp = project._getOb('.wf_policy_config', None)
        if wfp is not None:
            policy = wfp.getPolicyIn().getId()
            if policy.startswith('closed'):
                closed = 1

    feed_kwargs['closed'] = closed
    feed_kwargs['categories'] = categories
    feed_kwargs['summary'] = summary

    cabochon_utility = getUtility(ICabochonClient)
    cabochon_utility.send_feed_item(page.getId(), object_type, action, title,
                                    updated, username, **feed_kwargs)

    # older style notification; we should refactor these
    if project is not None:
        cabochon_utility.notify_wikipage_updated(project,
                                                 title,
                                                 url,
                                                 username)
