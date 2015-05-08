def wait_for_container(name, timeout):
    pass

def block_container():
    pass

def get_container_error(state, data):
    status_code = data.get('error_code')
    error = data.get('error')
    msg = ("%s - %s" % (status_code, error))
    raise(msg)