=====================
Client Authentication
=====================

When using LXD over https, LXD uses an asymmetric keypair for authentication.
The keypairs are added to the authentication database after entering a secret.
The secret can be the LXD trust password, when using LXD 5.0 or older, or a
trust token otherwise.


Generate a certificate
======================

To generate a keypair, you should use the `openssl` command. As an example:

.. code-block:: console

    openssl req -x509 -newkey rsa:2048 -keyout lxd.key -nodes -out lxd.crt -subj "/CN=lxd.local"

For more detail on the commands, or to customize the keys, please see the
documentation for the `openssl` command.


Authenticate a new keypair
==========================

If a client is created using this keypair, it would originally be "untrusted",
essentially meaning that the authentication has not yet occurred.

.. code-block:: python

    >>> from pylxd import Client
    >>> client = Client(
    ...     endpoint='http://10.0.0.1:8443',
    ...     cert=('lxd.crt', 'lxd.key'))
    >>> client.trusted
    False

In order to authenticate the client, pass the LXD instance's trust
password or token to `Client.authenticate`.
The secret provided will be use as a token if it has the proper format
and the server accepts tokens, otherwise it will be used as a password.
To force password authentication, `use_token_auth=False` can be used.

.. code-block:: python

    >>> client.authenticate('a-secret')
    >>> client.trusted
    >>> True

.. code-block:: python

    >>> token = '{"client_name":"foo","fingerprint":"abcd","addresses":["192.0.2.1:8443"],"secret":"I-am-a-secret","expires_at":"0001-01-01T00:00:00Z","type":""}'
    >>> client.authenticate(base64.b64encode(json.dumps(token).encode("utf-8")), use_token_auth=False) # Forces password authentication and fails
    >>> client.trusted
    >>> False
    >>> client.authenticate(base64.b64encode(json.dumps(token).encode("utf-8"))) # Token used as token
    >>> client.trusted
    >>> True
