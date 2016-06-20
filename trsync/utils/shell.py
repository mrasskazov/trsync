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


import subprocess
from trsync.utils import utils as utils


class Shell(object):

    def __init__(self, logger=None):
        if logger is None:
            self.logger = utils.logger.getChild('Shell')
        else:
            self.logger = logger.getChild('Shell')

    def shell(self, cmd, raise_error=True):
        self.logger.debug(cmd)
        process = subprocess.Popen(cmd,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   shell=True)
        out, err = process.communicate()
        self.logger.debug(out)
        if err:
            self.logger.error(err)
        exitcode = process.returncode
        if process.returncode != 0 and raise_error:
            msg = '"{cmd}" failed. Exit code == {exitcode}'\
                  '\n\nSTDOUT: \n{out}'\
                  '\n\nSTDERR: \n{err}'\
                  .format(**(locals()))
            self.logger.error(msg)
            raise RuntimeError(msg)
        return exitcode, out, err
