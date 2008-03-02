from OFS.SimpleItem import SimpleItem
from opencore.cabochon.interfaces import ICabochonClient
from zope.component import queryUtility
from zope.interface import implements

def setup_cabochon_mock(portal):
    # the cabochon utility is a local utility
    # so we need to remove it first if it already exists
    if queryUtility(ICabochonClient, context=portal):
        portal.utilities.manage_delObjects(['ICabochonClient'])

    site_manager = portal.getSiteManager()
    site_manager.registerUtility(ICabochonClient, StubCabochonClient())

class StubCabochonClient(SimpleItem):
    """stub class used to monkey patch cabochon for unit tests"""
    implements(ICabochonClient)

    def _stub(self, *args):
        print 'opencore.testing.utility.StubCabochonClient: args: %s' % (args,)

    notify_project_created = _stub
    notify_project_deleted = _stub
