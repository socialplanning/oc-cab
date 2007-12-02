from setuptools import setup, find_packages

version = '0.1'

setup(name='OpencoreTaskTracker',
      version=version,
      description="tasktracker yay",
      long_description="""\
""",
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Framework :: Zope2",
        "Framework :: Zope3",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='',
      author='Ethan Jucovy',
      author_email='ejucovy@openplans.org',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['opencore'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      [opencore.versions]
      OpencoreTaskTracker = opencore.tasktracker
      [opencore.plugin]
      configure.zcml = opencore.tasktracker:_configure
      """,
      )
