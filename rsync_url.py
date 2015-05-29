#-*- coding: utf-8 -*-

import logging
import re

logging.basicConfig(level='INFO')
logger = logging.getLogger('RsyncUrl')


class RsyncUrl(object):

    def __init__(self, remote_url):

        self.url = remote_url
        self._url_type = False

        self.regexps = {
            # ssh: [USER@]HOST:SRC
            'ssh': re.compile(
                r'^'
                r'(?P<user>[-\w]+@)?'
                r'(?P<host>[-\.\w]+){1}'
                r':'
                r'(?P<path>[\w/-]*){1}'
                r'$'
            ),
            # rsync: [USER@]HOST::SRC
            'rsync1': re.compile(
                r'^'
                r'(?P<user>[-\w]+@)?'
                r'(?P<host>[-\.\w]+){1}'
                r'::'
                r'(?P<path>[\w/-]*){1}'
                r'$'
            ),
            # rsync://[USER@]HOST[:PORT]/SRC
            'rsync2': re.compile(
                r'^rsync://'
                r'(?P<user>[-\w]+@)?'
                r'(?P<host>[-\.\w]+){1}'
                r'(?P<port>:[\d]+)?'
                r'(?P<path>[\w/-]*){1}'
                r'$'
            ),
            # local/path/to/directory
            'path': re.compile(
                r'^'
                r'(?P<path>[\w/-]+){1}'
                r'$'
            ),
        }

        self.match = self._get_matching_regexp()
        if self.match is None:
            self.user, self.host, self.port, self.path = None, None, None, None
        else:
            self._parse_rsync_url(self.match)

    def _get_matching_regexp(self):
        regexps = self._get_all_matching_regexps()
        regexps_len = len(regexps)
        #if regexps_len > 1:
        #    raise Exception('Rsync location {} matches with {} regexps {}'
        #                    ''.format(self.url, len(regexps), str(regexps)))
            # TODO: Possible may be better remove this raise and keep
            # only warning with request to fail bug. rsync will parse this
            # remote later
        if regexps_len != 1:
            logger.warn('Rsync location "{}" matches with {} regexps: {}.'
                        'Please fail a bug on {} if it is wrong.'
                        ''.format(self.url, len(regexps), str(regexps), '...'))
        if regexps_len == 0:
            self._url_type = None
            return None
        else:
            return regexps[0]

    def _get_all_matching_regexps(self):
        regexps = list()
        for url_type, regexp in self.regexps.items():
            match = regexp.match(self.url)
            if match is not None:
                if self.url_type is False:
                    self._url_type = url_type
                regexps.append(regexp)
            #print match, regexp.pattern
        return regexps

    def _parse_rsync_url(self, regexp):
        # parse remote url

        for match in re.finditer(regexp, self.url):

            self.path = match.group('path')
            if not self.path:
                self.path = '/'

            try:
                self.host = match.group('host')
            except IndexError:
                self.host = None

            try:
                self.user = match.group('user')
            except IndexError:
                self.user = None
            else:
                if self.user is not None:
                    self.user = self.user.strip('@')

            try:
                self.port = match.group('port')
            except IndexError:
                self.port = None
            else:
                if self.port is not None:
                    self.port = int(self.port.strip(':'))

    @property
    def url_type(self):
        return self._url_type
