=================
opencore.cabochon
=================

opencore.cabochon is opencore's helper package to CabochonClient. It contains
a number of event subscribers that fire messages off to cabochon at the
appropriate moments.

Since this package mostly consists of firing events to cabochon at the proper
time, we'll stub out the sending to cabochon, and verify that the right data
gets passed through::

We'll store the results in the list ``results``::

    >>> results = []

Create a stub cabochon client
    >>> from zope.interface import implements
    >>> from opencore.cabochon.interfaces import ICabochonClient
    >>> class StubCabochonClient(object):
    ...     implements(ICabochonClient)
    ...
    ...     def notify_project_deleted(self, id):
    ...         results.append(('proj_del', id))
    ...
    ...     def notify_project_created(self, id, creator):
    ...         results.append(('proj_create', id, creator))

Now we register it::

    >>> from zope.component import provideUtility
    >>> provideUtility(StubCabochonClient(), ICabochonClient)

And we register the event handlers::

    >>> from zope.component import provideHandler
    >>> from opencore.cabochon.subscribers import notify_project_deleted
    >>> provideHandler(notify_project_deleted)

Let's try create a dummy stub object, and say that it provides IProject::

    >>> from opencore.interfaces import IProject

    >>> class DummyProject(object):
    ...     implements(IProject)
    ...     id = 'dummyproject'

When we fire an event, then the subscribed event handler should send a message
with the cabochon client registered. In this case, it should append some data
to a ``result`` list above::

    >>> from zope.event import notify
    >>> from zope.app.container.contained import ObjectRemovedEvent
    >>> proj = DummyProject()

    >>> notify(ObjectRemovedEvent(proj, oldParent='', oldName=''))
    >>> results
    []
