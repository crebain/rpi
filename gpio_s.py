#!/usr/bin/env python

import sys, argparse
import select
import errno
import os
import subprocess
from datetime import datetime
from datetime import timedelta
import logging

def main(argv):
    parser = argparse.ArgumentParser (description="poll(2) for specified INPUT and execute CMD when it changes")
    parser.add_argument ('command', metavar='CMD', help='Command that wil be performed when INPUT changes')
    parser.add_argument ('arguments', nargs='*', metavar='ARGS', help='Optional arguments for CMD.')
    parser.add_argument ('-i', '--input', required=True, metavar='INPUT', type=argparse.FileType ('r'), help='The file to poll(2)')
    parser.add_argument ('-w', '--while', required=False, metavar='VALUE', default='1', help="Keeps CMD running while content of INPUT equals to VALUE. Default '1'")
    parser.add_argument ('-t', '--timeout', required=False, metavar='TIMEOUT', type=int, default=None, help='Timeout when CMD will be terminated, in seconds. Defaults to 0, i.e. CMD will be terminated when VALUE does not match specified.')
    parser.add_argument ('-v', '--verbosity', required=False, metavar='LEVEL', default=logging.getLevelName (logging.WARNING), help='Verbosity level. See http://docs.python.org/2/library/logging.html for possible values.')

    args = vars (parser.parse_args())

    input = args['input']
    command = " ".join ([args['command']] + args['arguments'])
    timeoutSeconds = args['timeout']
    timeout = timedelta (seconds=timeoutSeconds or 0)
    whileValue = args['while']

    logger = logging.getLogger(__package__)
    logger.setLevel(args['verbosity'])

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(args['verbosity'])

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

    logger.debug ('Input file is %s' % input)
    logger.debug ("Command to execute: '%(command)s'" % { 'command': command })

    pollTimeout = None
    if timeoutSeconds:
        pollTimeout = timeoutSeconds * 1000
        logger.debug ("Poll timeout %(pollTimeout)dms" % { 'pollTimeout': pollTimeout })

    process = None
    start = datetime.now()

    poller = select.poll()
    poller.register (input, select.POLLPRI)

    while (True):
        value = None
        list = poller.poll (pollTimeout)

        if not list:
            logger.debug ('poll timed out')

        for entry in list:
            fd = entry[0]
            events = entry[1]

            if events & select.POLLPRI:
                logger.debug ('poll: fd %d, events %d' % (fd, events))
                input.seek (0)
                value = input.read ().strip ()
                logger.debug ("read value '%s'" % value)


        result = None
        if None != process:
            result = process.poll()
            if None != result:
                logger.debug ('previous process finished with code %d' % result)
            else:
                logger.debug ('process #%d still active' % process.pid)


        if value == whileValue:
            start = datetime.now()

            if None == process or result != None:
                logger.debug ("starting process '%s'" % command)
                # Start a new process if old one already exited
                process = subprocess.Popen (command, shell=True)
                logger.debug ("process #%d started" % process.pid)
        else:
            if datetime.now() > start+timeout and None != process and None == process.poll():
                logger.debug ("terminating process #%d" % process.pid)
                process.terminate ()


    os.close (input)
    if None != process and None != process.poll():
        process.terminate ()



if __name__ == "__main__":
    main(sys.argv[1:])

