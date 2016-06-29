=====================
Client Authentication
=====================

When using LXD over https, LXD uses an asymmetric keypair for authentication.
The keypairs are added to the authentication database after entering the LXD
instance's "trust password".


Generate a certificate
======================

To generate a keypair, you should use the `openssl` command. As an example::

    openssl req -newkey rsa:2048 -nodes -keyout lxd.key -out lxd.csr
    openssl x509 -signkey lxd.key -in lxd.csr -req -days 365 -out lxd.crt

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

In order to authenticate the client, pass the lxd instance's trust
password to `Client.authenticate`

.. code-block:: python

    >>> client.authenticate('a-secret-trust-password')
    >>> client.trusted
    >>> True
