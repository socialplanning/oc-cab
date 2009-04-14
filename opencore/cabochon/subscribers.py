from Products.CMFCore.utils import getToolByName
from Products.listen.interfaces import IMailingList
from Products.listen.interfaces import IMemberLookup
from Acquisition import aq_inner
from cabochonclient import datetime_to_string
from datetime import datetime
from opencore.browser.base import IWikiContainer
from opencore.cabochon.interfaces import ICabochonClient
from opencore.interfaces import IOpenPage, IProject
from opencore.interfaces.adding import IAmAPeopleFolder
from opencore.interfaces.event import ILeftProjectEvent
from opencore.project.browser.projectinfo import ProjectInfo
from opencore.utils import interface_in_aq_chain
from rfc822 import parseaddr
from zope.app.container.contained import IObjectRemovedEvent
from zope.app.container.contained import IObjectAddedEvent
from zope.app.container.contained import IContainerModifiedEvent
from zope.component import adapter
from zope.component import getUtility


def ignore_container_modified(subscriber_fn):
    """
    We only care about object modification, not subobject adds.
    """
    def inner(obj, event=None):
        if IContainerModifiedEvent.providedBy(event):
            return
        return subscriber_fn(obj, event)
    return inner


def once_per_request(subscriber_fn):
    """
    Actually once per request per individual object and event type.
    """
    def inner(obj, event=None):
        ftool = getToolByName(obj, 'portal_factory')
        if ftool.isTemporary(obj):
            # we never want to fire events if we're still in the
            # factory tool
            return
        # sucks to use acquisition here, but we don't have a
        # get_request function yet
        request = obj.REQUEST
        # skip if further cab notifiers have been blocked
        if getattr(request, '_cab_prevent_further', False):
            return
        # check if this event / object pair has already happened
        attrname = '_cab_already_notified'
        fired_map = getattr(request, attrname, {})
        ob_path = '/'.join(obj.getPhysicalPath())
        event_id = None
        if event is not None:
            event_id = event.__class__.__name__
        fired_key = (ob_path, event_id)
        if fired_key in fired_map:
            return
        # prevent page edits from firing during page creation
        if ((ob_path, 'ObjectAddedEvent') in fired_map):
            return
        fired_map[fired_key] = None
        setattr(request, attrname, fired_map)
        return subscriber_fn(obj, event)
    return inner


def get_wf_state(ob, wf_id):
    return ob.workflow_history[wf_id][-1]['review_state']


def author_map_from_member(member):
    mtool = getToolByName(member, 'portal_membership')
    name = member.getProperty('fullname') or member.getId()
    uri = mtool.getHomeUrl(member.getId())
    email = member.getProperty('email')
    return {'name': name, 'uri': uri, 'email': email}


@ignore_container_modified
@once_per_request
def wikipage_notifier(page, event=None):
    project = ProjectInfo(page).project
    url = page.absolute_url()
    mtool = getToolByName(page, 'portal_membership')
    member = mtool.getAuthenticatedMember()
    author_map = author_map_from_member(member)
    title = page.title_or_id()
    updated = datetime_to_string(datetime.now())
    # XXX i18n.. bigger feedbacker issue, need to pass msgids into feedbacker?
    object_type = 'page'
    action = 'modified'
    if IObjectAddedEvent.providedBy(event):
        title = page.REQUEST.form.get('title') or title
        action = 'created'
    closed = 0
    categories = ['wiki']
    summary = "Wiki page %s: '%s'" % (action, title)

    feed_kwargs = dict(link=url)
    if project is not None:
        feed_kwargs['area'] = 'projects'
        proj_id = project.getId()
        feed_kwargs['project'] = proj_id
        categories.append('projects/%s' % proj_id)
        summary += " (in project '%s')" % project.title_or_id()
        state = get_wf_state(project, 'openplans_teamspace_workflow')
        closed = int(state == 'closed')

    if interface_in_aq_chain(page, IAmAPeopleFolder) is not None:
        # XXX... bit of a hack to prevent creation of a person's home
        # page from generating a feedbacker entry
        if (action == 'created' and
            page.getId() == '%s-home' % member.getId()):
            return
        feed_kwargs['area'] = 'people'

    if IWikiContainer is not None:
       wiki_container = interface_in_aq_chain(page, IWikiContainer)
       if wiki_container is not None:
           feed_kwargs['area'] = wiki_container.getId()

    feed_kwargs['summary'] = summary
    feed_kwargs['closed'] = closed
    feed_kwargs['categories'] = categories

    cabochon_utility = getUtility(ICabochonClient)
    cabochon_utility.send_feed_item(page.getId(), object_type, action, title,
                                    updated, author_map, **feed_kwargs)

    # bbb older-style notifiers, these really need to go away,
    # requires refactoring listeners that expect these events to be
    # fired.  i _think_ this is only twirlip
    username = member.getId()
    if action == 'created':
        parent = event.newParent
        cabochon_utility.notify_wikipage_created(parent, title, url, username)
    else:
        # modified
        if project is not None:
            cabochon_utility.notify_wikipage_updated(project,
                                                     title,
                                                     url,
                                                     username)


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


@adapter(IProject, IObjectRemovedEvent)
def notify_project_deleted(project, event=None):
    # project info passed to cabochon
    id = project.getId()

    cabochon_utility = getUtility(ICabochonClient)
    cabochon_utility.notify_project_deleted(id)


def project_mship_notifier(mship, event=None):
    team = mship.getTeam()
    username = mship.getId()
    mtool = getToolByName(mship, 'portal_membership')
    url = mtool.getHomeUrl(username)
    member = mship.getMember()
    author_map = author_map_from_member(member)
    memtitle = member.title_or_id()
    projtitle = team.title_or_id()
    # XXX i18n.. bigger feedbacker issue, need to pass msgids into feedbacker?
    action = 'joined'
    if ILeftProjectEvent.providedBy(event):
        action = 'left'
    summary = '%s %s project %s' % (memtitle, action, projtitle)
    updated = datetime_to_string(datetime.now())
    object_type = 'membership'
    team_state = get_wf_state(team, 'openplans_team_workflow')
    closed = int(team_state=='closed')
    categories = ['project', 'membership']
    feed_kwargs = dict(link=url)
    proj_id = team.getId()
    feed_kwargs['area'] = 'projects'
    feed_kwargs['project'] = proj_id
    feed_kwargs['summary'] = summary
    feed_kwargs['closed'] = closed
    feed_kwargs['categories'] = categories

    cabochon_utility = getUtility(ICabochonClient)
    cabochon_utility.send_feed_item(username, object_type, action, projtitle,
                                    updated, author_map, **feed_kwargs)


@ignore_container_modified
@once_per_request
def listen_message_notifier(msg, event=None):
    project = ProjectInfo(msg).project
    email = parseaddr(msg.from_addr)[1]
    memlookup = getUtility(IMemberLookup)
    username = memlookup.to_memberid(email)
    author_map = {}
    if username is None:
        author_map['email'] = email.decode('utf8')
        author_map['name'] = email.split('@')[0] + '@'
        author_map['name'] = author_map['name'].decode('utf8')
    else:
        mtool = getToolByName(msg, 'portal_membership')
        member = mtool.getMemberById(username)
        author_map = author_map_from_member(member)
    url = msg.absolute_url()
    title = msg.subject.encode('utf8')
    mlist = interface_in_aq_chain(msg, IMailingList)
    # XXX i18n.. bigger feedbacker issue, need to pass msgids into feedbacker?
    summary = "%s sent discussion message to '%s' forum" % (author_map['name'],
                                                            mlist.Title())
    updated = datetime_to_string(datetime.now())
    object_type = 'discussion message'
    action = 'sent'
    proj_state = get_wf_state(project, 'openplans_teamspace_workflow')
    closed = int(proj_state=='closed')
    proj_id = project.getId()
    categories = ['discussion', 'message', 'projects/%s' % proj_id]
    feed_kwargs = dict(link=url)
    feed_kwargs['area'] = 'projects'
    feed_kwargs['project'] = proj_id
    feed_kwargs['summary'] = summary
    feed_kwargs['closed'] = closed
    feed_kwargs['categories'] = categories

    cabochon_utility = getUtility(ICabochonClient)
    cabochon_utility.send_feed_item(username, object_type, action, title,
                                    updated, author_map, **feed_kwargs)


@once_per_request
def project_added_notifier(project, event=None):
    request = project.REQUEST
    url = project.absolute_url()
    mtool = getToolByName(project, 'portal_membership')
    member = mtool.getAuthenticatedMember()
    author_map = author_map_from_member(member)
    # moral equivalent of project.title_or_id()
    title = request.form.get('project_title') or event.newName
    if type(title) == unicode:
        title = title.encode('utf8')
    updated = datetime_to_string(datetime.now())
    # XXX i18n.. bigger feedbacker issue, need to pass msgids into feedbacker?
    object_type = 'project'
    action = 'created'
    closed = 0
    categories = ['project']
    summary = "Project %s: '%s'" % (action, title)

    feed_kwargs = dict(link=url)
    feed_kwargs['area'] = 'projects'
    proj_id = project.getId()
    feed_kwargs['project'] = proj_id
    categories.append('projects/%s' % proj_id)
    closed = int('closed' in request.form.get('workflow_policy', ''))

    feed_kwargs['summary'] = summary
    feed_kwargs['closed'] = closed
    feed_kwargs['categories'] = categories

    cabochon_utility = getUtility(ICabochonClient)
    cabochon_utility.send_feed_item(proj_id, object_type, action, title,
                                    updated, author_map, **feed_kwargs)
    # mark the request to prevent some of the other events from sending
    # any messages to feedbacker
    request._cab_prevent_further = True


def member_registered_notifier(event=None):
    member = aq_inner(event.member)
    username = member.getId()
    author_map = author_map_from_member(member)
    # mem folder not created yet, construct URL of where it will be
    mtool = getToolByName(member, 'portal_membership')
    url = '%s/%s' % (mtool.getMembersFolder().absolute_url(), username)
    # and fix up the author map uri
    author_map['uri'] = url
    memtitle = member.title_or_id()
    # XXX i18n.. bigger feedbacker issue, need to pass msgids into feedbacker?
    action = 'joined'
    portal = getToolByName(member, 'portal_url').getPortalObject()
    summary = '%s %s %s' % (memtitle, action, portal.Title())
    updated = datetime_to_string(datetime.now())
    object_type = 'member'
    categories = ['member']
    feed_kwargs = dict(link=url)
    feed_kwargs['summary'] = summary
    feed_kwargs['categories'] = categories

    cabochon_utility = getUtility(ICabochonClient)
    cabochon_utility.send_feed_item(username, object_type, action, memtitle,
                                    updated, author_map, **feed_kwargs)
