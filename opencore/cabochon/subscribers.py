from Products.CMFCore.utils import getToolByName
from Products.listen.interfaces import IMailingList
from Products.listen.interfaces import IMemberLookup
from cabochonclient import datetime_to_string
from datetime import datetime
from opencore.cabochon.interfaces import ICabochonClient
from opencore.interfaces import IOpenPage, IProject
from opencore.member.utils import member_path
from opencore.project.browser.projectinfo import ProjectInfo
from opencore.utils import interface_in_aq_chain
from rfc822 import parseaddr
from zope.app.container.contained import IObjectRemovedEvent
from zope.app.container.contained import IObjectAddedEvent
from zope.component import adapter
from zope.component import getUtility


def once_per_request(subscriber_fn):
    def inner(obj, event=None):
        # sucks to use acquisition here, but we don't have a
        # get_request function yet
        request = obj.REQUEST
        if getattr(request, '_cab_already_notified', False):
            return
        request._cab_already_notified = True
        return subscriber_fn(obj, event)
    return inner
        
def get_wf_state(ob, wf_id):
    return ob.workflow_history[wf_id][-1]['review_state']

def author_map_from_member(member):
    mtool = getToolByName(member, 'portal_membership')
    name = member.getProperty('fullname')
    uri = mtool.getHomeUrl(member.getId())
    email = member.getProperty('email')
    return {'name': name, 'uri': uri, 'email': email}

@once_per_request
def wikipage_notifier(page, event=None):
    project = ProjectInfo(page).project
    url = page.absolute_url()
    mtool = getToolByName(page, 'portal_membership')
    member = mtool.getAuthenticatedMember()
    author_map = author_map_from_member(member)
    title = page.title_or_id()
    updated = datetime_to_string(datetime.now())
    object_type = 'page'
    action = 'modified'
    if IObjectAddedEvent.providedBy(event):
        action = 'created'
    closed = 0
    categories = ['wiki']
    summary = "Wiki page %s: '%s'" % (action, title)

    feed_kwargs = dict(link=url)
    if project is not None:
        proj_id = project.getId()
        feed_kwargs['project'] = proj_id
        categories.append('projects/%s' % proj_id)
        summary += " (in project '%s')" % project.title_or_id()
        state = get_wf_state(project, 'openplans_teamspace_workflow')
        closed = int(state == 'closed')

    feed_kwargs['summary'] = summary
    feed_kwargs['closed'] = closed
    feed_kwargs['categories'] = categories

    cabochon_utility = getUtility(ICabochonClient)
    cabochon_utility.send_feed_item(page.getId(), object_type, action, title,
                                    updated, author_map, **feed_kwargs)

    # BBB older-style notifiers, these really need to go away,
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


def join_project_notifier(mship, event=None):
    team = mship.getTeam()
    username = mship.getId()
    mtool = getToolByName(mship, 'portal_membership')
    url = mtool.getHomeUrl(username)
    member = mship.getMember()
    author_map = author_map_from_member(member)
    memtitle = member.title_or_id()
    projtitle = team.title_or_id()
    title = '%s joined project %s' % (memtitle, projtitle)
    summary = title
    updated = datetime_to_string(datetime.now())
    object_type = 'membership'
    action = 'joined'
    team_state = get_wf_state(team, 'openplans_team_workflow')
    closed = int(team_state=='closed')
    categories = ['project', 'membership']
    feed_kwargs = dict(link=url)
    proj_id = team.getId()
    feed_kwargs['project'] = proj_id
    feed_kwargs['summary'] = summary
    feed_kwargs['closed'] = closed
    feed_kwargs['categories'] = categories

    cabochon_utility = getUtility(ICabochonClient)
    cabochon_utility.send_feed_item(username, object_type, action, title,
                                    updated, author_map, **feed_kwargs)


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
    feed_kwargs['project'] = proj_id
    feed_kwargs['summary'] = summary
    feed_kwargs['closed'] = closed
    feed_kwargs['categories'] = categories

    cabochon_utility = getUtility(ICabochonClient)
    cabochon_utility.send_feed_item(username, object_type, action, title,
                                    updated, author_map, **feed_kwargs)
