#! /usr/biun/python

import logging as mylog
import socket
import sys
import csv

class CreateList():

    def __init__(self, input_filename, output_filename):
        self.input_filename = input_filename
        self.output_filename = output_filename

    def openHostFile(self):
        name_list = []
        lines = open(self.input_filename, 'r')
        for line in lines:
            name_list.append(line.strip())
        return name_list

    def executeSocketCommand(self, hostname):
        try:
            output = socket.getaddrinfo(hostname, None)
            ip = output[2][4][0]
        except Exception as e:
            mylog.error("There was an error looking up host %s" % hostname)
            mylog.error("The error was %s:" % e)
            return False
        return ip

    def writeOutputFile(self, finished_list):
        mylog.debug("Opening file %s" % self.output_filename)
        with open(self.output_filename, 'wb') as csv_file:
            file_writer = csv.writer(csv_file)
            for key, value in finished_list.items():
                file_writer.writerow([key, value])
                mylog.debug("Wrote: %s, %s" % (key, value))
        return True

    def Execute(self):
        finished_list = {}
        mylog.info("Acquiring list of hostnames from file %s" % self.input_filename)
        hostname_list = self.openHostFile()
        mylog.info("Searching for IP addresses of hosts listed in file %s" % self.input_filename)
        for hostname in hostname_list:
            ip = self.executeSocketCommand(hostname)
            if ip:
                finished_list[hostname] = ip
            if ip == False:
                finished_list[hostname] = '??'
        mylog.debug("Collected ip list is:\n %s" % finished_list)
        mylog.info("List collection complete.")
        mylog.info("Writing list of hostnames and IPs to csv file")
        self.writeOutputFile(finished_list)
        mylog.info("Writing Complete.  See final output file: %s" % self.output_filename)

if __name__ == '__main__':
    import argparse
    #Parse command line arguments
    parser = argparse.ArgumentParser(add_help=True, description='Make a csv of [hostname,ip address] from a list of hostnames')
    parser.add_argument("-i", "--input", action="store", dest="input_filename", default=None, help="the file containing the list of filenames")
    parser.add_argument("-o", "--output", action="store", dest="output_filename", default=None, help="the desired output csv filename")
    parser.add_argument("--debug", action="store_true", dest="debug", default=False, help="display more verbose messages")

    args = parser.parse_args()
    debug = args.debug

    if debug:
        mylog.basicConfig(stream=sys.stdout, level=mylog.DEBUG, format='%(asctime)s %(levelname)s - %(message)s')
    else:
        mylog.basicConfig(stream=sys.stdout, level=mylog.INFO, format='%(asctime)s %(levelname)s - %(message)s')

    if not args.input_filename:
        print "Must provide input file of hostnames to read.  Use -h or --help to see help"
        sys.exit(1)
    if not args.output_filename:
        print "Must provide name for output csv file  Use -h or --help to see help"
        sys.exit(1)

    MakeMyGoddamnList = CreateList(args.input_filename, args.output_filename)
    try:
        MakeMyGoddamnList.Execute()
    except SystemExit:
        raise
    except KeyboardInterrupt:
        mylog.warning("Aborted by user")
        Abort()
        sys.exit(1)
    except:
        mylog.exception("Unhandled exception")
        sys.exit(1)

