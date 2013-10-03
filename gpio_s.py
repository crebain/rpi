#!/usr/bin/env python

import sys, argparse
import select
import errno
import os
import subprocess

def print_help(argv):
    print ('%(cmd)s -i <inputfile> -o <outputfile>' % { "cmd": argv[0] })

def main(argv):
    parser = argparse.ArgumentParser (description="poll(2) for specified INPUT and execute CMD when it changes")
    parser.add_argument ('command', metavar='CMD', help='Command that wil be performed when INPUT changes')
    parser.add_argument ('arguments', nargs='*', metavar='ARGS', help='Optional arguments for CMD. %s will be replaced by value read from INPUT. Use %% to display a single %.')
    parser.add_argument ('-i', '--input', required=True, metavar='INPUT', type=argparse.FileType ('r'), help='The file handle to poll(2)')
    args = parser.parse_args()

    print ('Input file is %s' % args.input)
    command = " ".join ([args.command] + args.arguments)
    print ("Command to execute: '%(command)s'" % { 'command': command })

    while (True):
        poller = select.poll()
        poller.register (args.input, select.POLLPRI)
        list = poller.poll ()

        for entry in list:
            fd = entry[0]
            events = entry[1]

            if events & select.POLLPRI:
                args.input.seek (0)
                value = args.input.read (1)
                subprocess.call (command % value, shell=True)


    os.close (args.input)



if __name__ == "__main__":
    main(sys.argv[1:])

