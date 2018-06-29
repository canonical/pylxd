Operations
==========

`Operation` objects detail the status of an asynchronous operation that is
taking place in the background.  Some operations (e.g. image related actions)
can take a long time and so the operation is performed in the background.  They
return an operation `id` that may be used to discover the state of the
operation.


Manager methods
---------------

Operations can be queried through the following client manager methods:

  - `get()` - Get a specific operation, by its id.
  - `wait_for_operation()` - get an operation, but wait until it is complete
    before returning the operation object.


Operation object methods
------------------------

  - `wait()` - Wait for the operation to complete and return.  Note that this
    can raise a `LXDAPIExceptiion` if the operations fails.

