from cabochonclient import CabochonClient, datetime_to_string
from datetime import datetime
from opencore.cabochon.interfaces import ICabochonClient
from opencore.configuration.utils import product_config
from opencore.utility.interfaces import IProvideSiteConfig
from threading import Thread, Lock
from zope.interface import implements
from zope.component import getUtility
from Products.CMFCore.utils import getToolByName

class CabochonConfigError(Exception):
    """Error in cabochon configuration"""


class CabochonUtility(object):
    """utility to handle communications with cabochon"""

    implements(ICabochonClient)

    def __init__(self):
        """initialize cabochon utility with portal context"""

        # get the cabochon username and password
        cabochon_user_info_file = product_config('cabochon_user_info',
                                                 'opencore.nui')
        if not cabochon_user_info_file:
            raise CabochonConfigError('no cabochon_user_info file specified in zope.conf opencore.nui')

        try:
            f = open(cabochon_user_info_file)
            username, password = f.read().strip().split(':', 1)
            f.close()
        except IOError:
            raise CabochonConfigError('bad cabochon_user_info file specified in zope.conf opencore.nui')

        # get cabochon_messages filesystem location from configuration
        cabochon_messages_dir = product_config('cabochon_messages',
                                               'opencore.nui')
        if not cabochon_messages_dir:
            raise CabochonConfigError('no cabochon_messages directory specified in zope.conf opencore.nui')

        # Stash config settings for later.
        self.cabochon_messages_dir = cabochon_messages_dir
        self.username = username
        self.password = password
        self.lock = Lock()


    def _initialize_client(self):
        # Initialize the cabochon client.
        
        # We don't want this in __init__, to avoid depending on a
        # specific zcml load order: we need an IProvideSiteConfig
        # utility to be set up by now, and if we did this in __init__,
        # that would have to happen before this package's zcml could
        # load, because it creates a global CabochonUtility instance.

        cabochon_client = CabochonClient(self.cabochon_messages_dir,
                                         self.cabochon_uri,
                                         self.username,
                                         self.password)
        # initialize and start the thread
        sender = cabochon_client.sender()
        thread = Thread(target=sender.send_forever)
        thread.setDaemon(True)
        thread.start()
        return cabochon_client

    @property
    def cabochon_client(self):
        self.lock.acquire()
        try:
            if not hasattr(self, '_cabochon_client'):
                self._cabochon_client = self._initialize_client()
        finally:
            self.lock.release()
        return self._cabochon_client
            
    @property
    def cabochon_uri(self):
        cabochon_uri = getUtility(IProvideSiteConfig).get('cabochon uri')
        cabochon_uri = cabochon_uri.strip()
        if not cabochon_uri:
            raise CabochonConfigError('invalid empty cabochon uri or cabochon uri not set')
        return cabochon_uri

    def send_feed_item(self, id, obtype, action, title, updated, member,
                       **kwargs):
        """Sends feed item data intended for the feed store.

        If kwargs contains any of the following keys, the key / value
        pair will be passed along in the event message.  Unrecognized
        keys will be ignored.
        """
        mtool = getToolByName(member, 'portal_membership')
        author_map = {'name': member.getProperty('fullname'),
                      'uri': mtool.getHomeUrl(member.getId()),
                      'email': member.getProperty('email')}
        msg_data = dict(title=title, updated=updated, author=author_map,
                        object_type=obtype, action=action)
        addl_msg_data_keys = ('categories',
                              'summary',
                              'content',
                              'link',
                              'published', # datetime
                              'rights',
                              'project',
                              'closed', # 0 or 1 as boolean values
                         )
        for key in addl_msg_data_keys:
            value = kwargs.get(key)
            if value is not None:
                msg_data[key] = value

        event_name = 'send_feed_item'
        uri = '%s/event/fire_by_name/%s' % (self.cabochon_uri, event_name)
        self.cabochon_client.send_message(msg_data, uri, ensure_ascii=False)

    def notify_project_created(self, id, creatorid):
        event_name = 'create_project'
        uri = '%s/event/fire_by_name/%s' % (self.cabochon_uri, event_name)
        self.cabochon_client.send_message(dict(id=id, creator=creatorid), uri)

    def notify_project_deleted(self, id):
        event_name = 'delete_project'
        uri = '%s/event/fire_by_name/%s' % (self.cabochon_uri, event_name)
        self.cabochon_client.send_message(dict(id=id), uri)

    def notify_wikipage_created(self, project, page_title, page_url, creatorid):
        event_name = 'create_page'
        uri = '%s/event/fire_by_name/%s' % (self.cabochon_uri, event_name)
        self.cabochon_client.send_message(dict(
                url = page_url,
                context = project.absolute_url() + "/security-context",
                categories=['projects/' + project.id, 'wiki'],
                title = page_title,
                event_class = [['page_edited', creatorid]],
                user = creatorid,
                date = datetime_to_string(datetime.now())), uri)

    def notify_wikipage_deleted(self, page_url, actorid):
        event_name = 'delete_page'
        uri = '%s/event/fire_by_name/%s' % (self.cabochon_uri, event_name)
        self.cabochon_client.send_message(dict(
                url = page_url,
                user = actorid,
                date = datetime_to_string(datetime.now())), uri)

    def notify_wikipage_updated(self, project, page_title, page_url, actorid):
        event_name = 'edit_page'
        uri = '%s/event/fire_by_name/%s' % (self.cabochon_uri, event_name)
        now = datetime_to_string(datetime.now())
        self.cabochon_client.send_message(dict(
                url = page_url,
                context = project.absolute_url() + "/security-context",
                categories=['projects/' + project.id, 'wiki'],
                title = page_title,
                event_class = [['page_edited', actorid]],
                user = actorid,
                date = now,
                ), uri)
