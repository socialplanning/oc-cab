import logging
from opencore.configuration.setuphandlers import setuphandler
from opencore.configuration.setuphandlers import register_local_utility
from opencore.cabochon.interfaces import ICabochonClient
from opencore.cabochon.client import CabochonConfigError
from opencore.cabochon.client import CabochonUtility
import traceback

logger = logging.getLogger('opencore.cabochon.configuration.setuphandlers')

@setuphandler
def install_cabochon_utility(portal, out):
    try:
        factory_fn = lambda:CabochonUtility(portal)
        register_local_utility(portal, out,
                               ICabochonClient, CabochonUtility,
                               factory_fn)
    except ValueError:
        logger.info(traceback.print_exc())
    except CabochonConfigError:
        logger.info(traceback.print_exc())
