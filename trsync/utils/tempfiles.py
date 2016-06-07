# -*- coding: utf-8 -*-

# Copyright (c) 2015-2016, Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import shutil
import tempfile

from trsync.utils import utils as utils


class TempFiles(object):
    def __init__(self):
        self.logger = utils.logger.getChild('TempFiles')
        self._temp_dirs = list()
        self.empty_dir

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.__del__()

    def __del__(self):
        for d in self._temp_dirs:
            if os.path.isdir(d):
                shutil.rmtree(d)
                self.logger.debug('Removed temporary directory "{}"'.format(d))

    @property
    def empty_dir(self):
        if self.__dict__.get('_empty_dir') is None:
            self._empty_dir = self.get_temp_dir()
        return self._empty_dir

    def get_temp_dir(self, subdirs=None):
        temp_dir = tempfile.mkdtemp()
        self._temp_dirs.append(temp_dir)
        msg = 'Created temporary directory "{}"'.format(temp_dir)
        if subdirs:
            self.create_subdirs(subdirs, temp_dir)
            msg += ' including subdirs "{}"'.format(subdirs)
        self.logger.debug(msg)
        return temp_dir

    @property
    def last_temp_dir(self):
        return self._temp_dirs[-1]

    def create_subdirs(self, subdirs, temp_dir):
        if not os.path.isdir(temp_dir):
            temp_dir = self.get_temp_dir()
        if subdirs is not None:
            if type(subdirs) == str:
                _ = subdirs
                subdirs = list()
                subdirs.append(_)
            if type(subdirs) in (list, tuple):
                for s in subdirs:
                    os.makedirs(os.path.join(temp_dir,
                                             s.strip(os.path.sep + '~')))
            else:
                raise Exception('subdirs should be tuple or list of strings, '
                                'but currentry subdirs == {}'.format(subdirs))
        return temp_dir

    def get_symlink_to(self, target, temp_dir=None, name=None):
        if name:
            subdirs, linkname = os.path.split(name)
        if temp_dir is None:
            temp_dir = self.get_temp_dir(subdirs=subdirs)
        else:
            linkname = tempfile.mktemp(dir=temp_dir)
        os.symlink(target.strip(os.path.sep), linkname)
        self.logger.debug('Creates temporary symlink "{} -> {}"'
                          ''.format(linkname, target))
        return linkname

    def get_file(self, content='', temp_dir=None, name=None):
        if temp_dir is None:
            temp_dir = self.get_temp_dir()
        filename = tempfile.mktemp(dir=temp_dir)
        with open(filename, 'w') as outfile:
            outfile.write(content)
        self.logger.debug('Creates temporary file "{}"'.format(filename))
        return filename
