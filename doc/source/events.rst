Events
======

LXD provides an `/events` endpoint that is upgraded to a streaming websocket
for getting LXD events in real-time. The :class:`~pylxd.Client`'s `events`
method will return a websocket client that can interact with the
web socket messages.

.. code-block:: python

    >>> ws_client = client.events()
    >>> ws_client.connect()
    >>> ws_client.run()

A default client class is provided, which will block indefinitely, and
collect all json messages in a `messages` attribute. An optional 
`websocket_client` parameter can be provided when more functionality is
needed. The `ws4py` library is used to establish the connection; please
see the `ws4py` documentation for more information.
