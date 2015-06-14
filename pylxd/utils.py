def wait_for_container(name, timeout):
    pass

def block_container():
    pass

def get_lxd_error(state, data):
    status_code = data.get('error_code')
    error = data.get('error')
    error_code = int(data.get('error_code'))
    if state == 404:
        return False
    else:
        ''' If it is much worse than that.'''
        msg = ("Error %s - %s." % (status_code, error))
        raise Exception(msg)
