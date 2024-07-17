Certificates
============

Certificates are used to manage authentications in LXD. Certificates are
not editable. They may only be created or deleted. None of the certificate
operations in LXD are asynchronous.

Manager methods
---------------

Certificates can be queried through the following client manager
methods:

  - `all()` - Retrieve all certificates.
  - `get()` - Get a specifit certificate, by its fingerprint.
  - `create()` - Create a new certificate. This method requires a first argument
    that is a secret and a second containing the cert data, in binary format.
    The secret can be the LXD trust password, when using LXD 5.0 or older,
    or a trust token otherwise.


Certificate attributes
----------------------

Certificates have the following attributes:

  - `fingerprint` - The fingerprint of the certificate. Certificates
    are keyed off this attribute.
  - `certificate` - The certificate itself, in PEM format.
  - `type` - The certificate type (currently only "client")
