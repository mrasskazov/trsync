#-*- coding: utf-8 -*-

import subprocess
import utils


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
        exitcode = process.returncode
        if process.returncode != 0 and raise_error:
            msg = '"{cmd}" failed. Exit code == {exitcode}'\
                  '\n\nSTDOUT: \n{out}'\
                  '\n\nSTDERR: \n{err}'\
                  .format(**(locals()))
            self.logger.error(msg)
            raise RuntimeError(msg)
        return exitcode, out, err
