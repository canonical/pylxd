def wait_for_container(name, timeout):
    pass

def block_container():
    pass

def get_lxd_error(state, data):
    status_code = data.get('error_code')
    error = data.get('error')
    msg = ("Error %s - %s." % (status_code, error))
    raise Exception(msg)