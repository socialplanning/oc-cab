from zope.interface import Interface

class ICabochonClient(Interface):
    def __init__(self, conf):
        pass

    def send_feed_item(id, obtype, action, title, updated, author_map,
                       **kwargs):
        """send feed item data to feedbacker"""

    def notify_project_created(id, creator):
        """send a project created message to cabochon"""

    def notify_project_deleted(id):
        """send a project deleted message to cabochon"""

    def notify_wikipage_created(project, page_title, page_url, creatorid):
        """Send a page created message to cabochon"""

    def notify_wikipage_updated(project, page_title, page_url, userid):
        """Send a page updated message to cabochon"""

    def notify_wikipage_deleted(page_url, userid):
        """Send a page updated message to cabochon"""
