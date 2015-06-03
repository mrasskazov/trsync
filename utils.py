#-*- coding: utf-8 -*-


import logging
import os
import time


logging.basicConfig()
logger = logging.getLogger('safe_rsync')

loglevel = os.environ.get('LOGLEVEL', 'INFO')
if loglevel not in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
    logger.warn('LOGLEVEL environment variable has wrong value=={}. Using '
                '"INFO" by default.'.format(loglevel))
    loglevel = 'INFO'
logger.setLevel(loglevel)


def logged(logger=None):
    if logger is None:
        logger = globals().get('logger')

    def wrap(f):
        def wrapped_f(*args, **kwargs):
            logger.debug('Starting {}({}, {}) (defaults: {})'
                         ''.format(f.__name__,
                                   str(args),
                                   str(kwargs),
                                   str(f.__defaults__))
                         )
            r = f(*args, **kwargs)
            logger.debug('{} done with result "{}".'.
                         format(f.__name__, str(r)))
            return r
        return wrapped_f
    return wrap


# retry decorator
def retry(expected_status, timeout=None, attempts=None):

    def wrap(f):
        def wrapped_f(*args, **kwargs):
            r = f(*args, **kwargs)
            return r
        return wrapped_f
    return wrap


class ResultNotProduced(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Retry(object):
    """
    Waits while the function reaches the specified status.

    :param function: function that returns some status
    :param expected_status: status the machine should turn to
    :param attempts: how many times to check status
    :param timeout: timeout in seconds before attempts
    :return: True if node moves to the specified status, False otherwise
    :Examples:
    Retry(timeout=3, attempts=10).wait(function, result, param1, param2)
    Retry().wait_result(function, result, param1, param2)
    """

    def __init__(self, timeout=5, attempts=10):
        self.timeout = timeout
        self.attempts = attempts
        self.logger = globals().get('logger').getChild('Retry')

    def wait_result(self, function, expected_result, *args, **kwargs):

        self.logger.debug('Wait for {}() == {}...'
                          ''.format(function.__name__, str(expected_result)))

        @logged(self.logger)
        def f():
            return function(*args, **kwargs)

        attempt = 1
        while attempt <= self.attempts:
            try:
                result = f()
            except Exception as e:
                self.logger.error('Exception on function {}: {}'
                                  ''.format(function.__name__, str(e)))
                raise
            else:
                if result == expected_result:
                    self.logger.debug('Got on attempt #{}:'.format(attempt))
                    return result
                attempt += 1
                time.sleep(self.timeout)

        raise ResultNotProduced('Result "{}" was not produced during '
                                '{} attempts.'
                                ''.format(expected_result, attempt - 1))
