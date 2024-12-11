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
    ...     endpoint='https://10.0.0.1:8443',
    ...     cert=('lxd.crt', 'lxd.key'))
    >>> client.trusted
    False

In order to authenticate the client, pass the LXD instance's trust
password or token to `Client.authenticate`

.. code-block:: python

    >>> client.authenticate('a-secret')
    >>> client.trusted
    >>> True
