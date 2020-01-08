from setuptools import setup, find_packages

version = '0.2dev'

setup(name='oc-cab',
      version=version,
      description="opencore cabochon client package",
      long_description="""\
""",
      # Get more strings from https://pypi.org/pypi?:action=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Framework :: Zope2",
        "Framework :: Zope3",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='opencore cabochon client',
      author='The Open Planning Project',
      author_email='',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['opencore'],
      include_package_data=True,
      zip_safe=False,
      dependency_links=[
          'http://github.com/socialplanning/CabochonClient/tarball/master#egg=cabochonclient-dev',
      ],
      install_requires=[
          'setuptools',
          'CabochonClient',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [opencore.versions]
      oc-cab = opencore.cabochon
      [topp.zcmlloader]
      opencore = opencore.cabochon
      """,
      )
