from zope.testing import doctest
import unittest
import doctest


optionflags = doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")

def test_suite():

    from pprint import pprint

    globs = locals()

    readme = doctest.DocFileSuite("README.txt", 
                                  optionflags=optionflags,
                                  package='opencore.cabochon',
                                  globs = globs,
                                  )

    suites = (readme,)
    return unittest.TestSuite(suites)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
