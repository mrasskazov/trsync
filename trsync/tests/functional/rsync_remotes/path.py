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

import logging
import os
import shutil


logging.basicConfig()
log = logging.getLogger(__name__ + 'Instance')
log.setLevel('DEBUG')


class Instance(object):

    """Provide an temporal rsync daemon on custom port"""

    def __init__(self, name):
        self._log = log.getChild(name)
        self._name = name
        self._root_dir = '/tmp/trsync_test/path'
        self._data_dir = os.path.join(self._root_dir, name)

        self._init_files()

    def stop(self):
        if os.path.isdir(self._data_dir):
            self._log.debug('Removed directory "%s"', self._data_dir)
            shutil.rmtree(self._data_dir)

    @property
    def url(self):
        return self.path

    @property
    def path(self):
        return self._data_dir

    def _init_files(self):
        if os.path.isdir(self._data_dir):
            self._log.debug('Directory %s already exists. Removing...'
                            '', self._data_dir)
            shutil.rmtree(self._data_dir)
        self._log.debug('Creating rsync local directory %s', self.path)
        os.makedirs(self.path)
