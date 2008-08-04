from zope.interface import Interface

class ICabochonClient(Interface):
    def __init__(self, conf):
        pass

    def notify_project_created(self, id, creator):
        """send a project created message to cabochon"""

    def notify_project_deleted(self, id):
        """send a project deleted message to cabochon"""

    def notify_wikipage_created(self, project, page_title, page_url, creatorid):
        """Send a page created message to cabochon"""

    def notify_wikipage_updated(self, project, page_title, page_url, userid):
        """Send a page updated message to cabochon"""

    def notify_wikipage_deleted(self, page_url, userid):
        """Send a page updated message to cabochon"""
