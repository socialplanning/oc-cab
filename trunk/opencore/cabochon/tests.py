from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
from opencore.testing import dtfactory as dtf
from opencore.testing.layer import MockHTTPWithContent
from zope.testing import doctest
import unittest


optionflags = doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")

def test_suite():

    from pprint import pprint
    from opencore.cabochon.testing.utility import pop_test_log

    globs = locals()

    readme = dtf.ZopeDocFileSuite("README.txt", 
                                  optionflags=optionflags,
                                  package='opencore.cabochon',
                                  test_class=FunctionalTestCase,
                                  globs = globs,
                                  layer = MockHTTPWithContent,
                                  )

    suites = (readme,)
    return unittest.TestSuite(suites)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
