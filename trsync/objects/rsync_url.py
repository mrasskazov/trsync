# -*- coding: utf-8 -*-

import os
import re

from trsync.utils import utils as utils


logger = utils.logger.getChild('RsyncUrl')


class RsyncUrl(object):

    def __init__(self, remote_url):

        if not remote_url:
            msg = 'Specified rsync url == "{}"'.format(remote_url)
            logger.error(msg)
            raise Exception(msg)

        self._url = remote_url
        self._url_type = False
        self._sep = '/'

        self.pattern_tpls = {
            'protocol': r'((?P<protocol>^[^/:]+)://)',
            'user': r'((?P<user>[^@/:]+)@)',
            'host': r'(?P<host>[^@:/]+)',
            'port': r'(:(?P<port>[^@:/]+))',
            'module': r'((?P<module>[^@:/]+)/?)',
            'path': r'(?P<path>[^@:]*$)',
        }

        self.patterns = {
            # ssh: [USER@]HOST:SRC
            'ssh': re.compile(
                '^{user}?{host}:(?!//){path}?$'
                ''.format(**self.pattern_tpls)
            ),
            # rsync: [USER@]HOST::SRC
            'rsync1': re.compile(
                '^{user}?{host}(::(?!/){module}?){path}?$'
                ''.format(**self.pattern_tpls)
            ),
            # rsync://[USER@]HOST[:PORT]/SRC
            'rsync2': re.compile(
                '^{protocol}{user}?{host}{port}?(/{module})?{path}?$'
                ''.format(**self.pattern_tpls)
            ),
            # local/path/to/directory
            'path': re.compile(
                '^{path}$'
                ''.format(**self.pattern_tpls)
            ),
        }

        self.templates = {
            # ssh: [USER@]HOST:SRC
            'ssh': ('{user}@', '{host}:', '{path}'),
            # rsync: [USER@]HOST::SRC
            'rsync1': ('{user}@', '{host}::', '{module}', '/{path}'),
            # rsync://[USER@]HOST[:PORT]/SRC
            'rsync2': ('{protocol}://', '{user}@', '{host}', ':{port}',
                       '/{module}', '/{path}'),
            # local/path/to/directory
            'path': ('{path}', ),
        }

        self._match = self._get_matching_pattern()
        if self.match is None:
            self._parsed_url = utils.bunch()
            self._parsed_url.protocol = None,
            self._parsed_url.user = None,
            self._parsed_url.host = None,
            self._parsed_url.port = None,
            self._parsed_url.module = None,
            self._parsed_url.path = None,
        else:
            self._parse_rsync_url(self.match)

    def _get_matching_pattern(self):
        patterns = self._get_all_matching_patterns()
        patterns_len = len(patterns)
        if patterns_len != 1:
            logger.warn('Rsync location "{}" matches with {} patterns: {}.'
                        'Please file a bug on {} if it is wrong.'
                        ''.format(self.url,
                                  len(patterns),
                                  [str(_.pattern) for _ in patterns],
                                  '...'))
        if patterns_len == 0:
            self._url_type = None
            return None
        else:
            return patterns[0]

    def _get_all_matching_patterns(self):
        patterns = list()
        for url_type, pattern in self.patterns.items():
            match = pattern.match(self.url)
            if match is not None:
                if self.url_type is False:
                    self._url_type = url_type
                patterns.append(pattern)
        return patterns

    def _parse_rsync_url(self, pattern):
        # parse remote url

        match = pattern.match(self._url)
        self._parsed_url = utils.bunch(match.groupdict())

        if self.url_type == 'ssh':
            if self._parsed_url.path == '':
                self._parsed_url.path = '~'

            if self.path.startswith('/'):
                self._parsed_url.rootpath = '/'
            else:
                self._parsed_url.rootpath = '~/'

        elif self.url_type.startswith('rsync'):
            if self._parsed_url.module:
                if self._parsed_url.path == '':
                    self._parsed_url.path = '/'
                self._parsed_url.rootpath = '/'
            else:
                self._parsed_url.path = None

            if self.url_type == 'rsync2':
                if self.protocol != 'rsync':
                    msg = 'Wrong URL protocol == "{}"'.format(self.protocol)
                    logger.error(msg)
                    raise Exception(msg)

        elif self.url_type == 'path':
            self._sep = os.path.sep
            self._parsed_url.rootpath = self.a_dir(self.path)

    @property
    def match(self):
        return self._match

    @property
    def url_type(self):
        return self._url_type

    @property
    def url(self):
        return self._url

    @property
    def protocol(self):
        return self._parsed_url.get('protocol', None)

    @property
    def user(self):
        return self._parsed_url.get('user', None)

    @property
    def host(self):
        return self._parsed_url.get('host', None)

    @property
    def port(self):
        return self._parsed_url.get('port', None)

    @property
    def module(self):
        return self._parsed_url.get('module', None)

    @property
    def path(self):
        return self._parsed_url.get('path', '')

    @property
    def sep(self):
        return self._sep

    @property
    def root(self):

        templates = {
            # ssh: [USER@]HOST:SRC
            'ssh': ('{user}@', '{host}:', '{rootpath}'),
            # rsync: [USER@]HOST::SRC
            'rsync1': ('{user}@', '{host}::', '{module}'),
            # rsync://[USER@]HOST[:PORT]/SRC
            'rsync2': ('{protocol}://', '{user}@', '{host}', ':{port}',
                       '/{module}'),
            # local/path/to/directory
            'path': ('{rootpath}', ),
        }
        return self.by_template(templates[self.url_type])

    @property
    def netloc(self):

        templates = {
            # ssh: [USER@]HOST:SRC
            'ssh': ('{user}@', '{host}:'),
            # rsync: [USER@]HOST::SRC
            'rsync1': ('{user}@', '{host}::', '{module}'),
            # rsync://[USER@]HOST[:PORT]/SRC
            'rsync2': ('{protocol}://', '{user}@', '{host}', ':{port}',
                       '/{module}'),
            # local/path/to/directory
            'path': ('', ),
        }
        return self.by_template(templates[self.url_type])

    @property
    def parsed_url(self):
        if self.url_type is None:
            return None
        parsed_dict = utils.bunch()
        for part in ('protocol', 'user', 'host', 'port', 'module', 'path',
                     'rootpath'):
            for tplpart in self.templates[self.url_type]:
                if '{' + part + '}' in tplpart:
                    value = self._parsed_url.get(part)
                    if value:
                        parsed_dict[part] = value
        return parsed_dict

    def by_template(self, template_list):
        template = ''
        for part in ('protocol', 'user', 'host', 'port', 'module', 'path',
                     'rootpath'):
            for tplpart in template_list:
                if '{' + part + '}' in tplpart:
                    if self._parsed_url.get(part):
                        template += tplpart
        return template.format(**self._parsed_url)

    @property
    def is_valid(self):
        if self.match is None:
            return False
        if self.path in (None, False):
            return False
        if self.url_type != 'path':
            if self.host in ('', None, False):
                return False
        if self.url_type.startswith('rsync'):
            if self.module is None:
                return False
        return True

    def _fn_join(self, *parts):
        ''' Joins filenames with ignoring empty parts (None, '', etc)'''

        parts = [_ for _ in parts if _]

        if len(parts) > 0:
            if parts[-1].endswith(self.sep):
                isdir = True
            else:
                isdir = False
            first, parts = parts[0], parts[1:]
        else:
            return ''

        if first is None:
            first = ''
        if len(first) > 1:
            while first.endswith(self.sep):
                first = first[:-1]

        subs = self.sep.join([_ for _ in parts if _]).split(self.sep)
        subs = [_ for _ in subs if _]

        result = re.sub(r'^//', r'/', self.sep.join([first, ] + subs))
        result = re.sub(r'([^:])//', r'\1/', result)
        if not result.endswith(self.sep) and isdir:
            result += self.sep
        return result

    def join(self, *parts):
        return self._fn_join(*parts)

    def urljoin(self, *parts):
        return self.join(self.by_template(self.templates[self.url_type]),
                         *parts)

    def a_dir(self, *path):
        result = self._fn_join(*path)
        if not result.endswith('/'):
            result += '/'
        return result

    def url_dir(self, *path):
        return self.a_dir(self.by_template(self.templates[self.url_type]),
                          *path)

    def a_file(self, *path):
        result = self._fn_join(*path)
        if len(result) > 1:
            while result.endswith(self.sep):
                result = result[:-1]
        return result

    def url_file(self, *path):
        return self.a_file(self.by_template(self.templates[self.url_type]),
                           *path)
