=====
Usage
=====

Once you have pylxd installed, you're ready to start interacting with LXD:

.. code-block:: python

    import uuid
    from pylxd import api

    # Let's pick a random name, avoiding clashes
    CONTAINER_NAME = str(uuid.uuid1())

    lxd = api.API()

    try:
        lxd.container_defined(CONTAINER_NAME)
    except Exception as e:
        print("Container does not exist: %s" % e)

    config = {'name': CONTAINER_NAME,
              'source': {'type': 'none'}}
    lxd.container_init(config)
    if lxd.container_defined(CONTAINER_NAME):
        print("Container is running")
    else:
        print("Whoops - please report a bug!")
    containers = lxd.container_list()
    for x in containers:
        lxd.container_destroy(x)
