from cabochonclient import CabochonClient
from opencore.cabochon.interfaces import ICabochonClient
from opencore.configuration.utils import product_config
from opencore.utility.interfaces import IProvideSiteConfig
from threading import Thread
from zope.interface import implements
from zope.component import getUtility

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

        
        # initialize cabochon client
        self.cabochon_client = CabochonClient(cabochon_messages_dir,
                                         cabochon_uri,
                                         username,
                                         password)

        # initialize the thread
        sender = self.cabochon_client.sender()

        # and start it
        thread = Thread(target=sender.send_forever)
        thread.setDaemon(True)
        thread.start()

    @property
    def cabochon_uri(self):
        cabochon_uri = getUtility(IProvideSiteConfig).get('cabochon uri')
        cabochon_uri = cabochon_uri.strip()
        if not cabochon_uri:
            raise CabochonConfigError('invalid empty cabochon uri or cabochon uri not set')
        return cabochon_uri

    def notify_project_created(self, id, creatorid):
        event_name = 'create_project'
        uri = '%s/event/fire_by_name/%s' % (self.cabochon_uri, event_name)
        self.cabochon_client.send_message(dict(id=id, creator=creatorid), uri)

    def notify_project_deleted(self, id):
        event_name = 'delete_project'
        uri = '%s/event/fire_by_name/%s' % (self.cabochon_uri, event_name)
        self.cabochon_client.send_message(dict(id=id), uri)
