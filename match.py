#! /bin/usr/python

import sys
import argparse


def readFile(filename):
    name_list = []
    lines = open(filename, 'r')
    for line in lines:
        name_list.append(line.strip())
#    print name_list
    return name_list

def number_count(filename_A, filename_B, ymatch, nmatch):
    count = 0
    no_m_count = 0
    match_list = []
    no_match_list = []
    check_list_A = readFile(filename_A)
    check_list_B = readFile(filename_B)
    for n_A in check_list_A:
        check_int = is_number(n_A)
        if not check_int:
            found_match = False
            for n_B in check_list_B:
                #chuck = n_B.split('-')
                #ends = chuck[1].strip('.jpg')
                #chaff = str(int(ends))
                if n_A == n_B:
                    new_line = "%s matches %s" % (n_A, n_B)
                    match_list.append(new_line)
                    found_match = True
                    count = count + 1
            if not found_match:
                nmatch_line =  "%s has no match" % n_A
                no_match_list.append(nmatch_line)
                no_m_count = no_m_count + 1
    if not nmatch:
        for m in sorted(match_list):
            print m 
        print "There are %s that match, in total." % count
    if not ymatch:
        for n in sorted(no_match_list):
            print n
        print "There are %s that don't match, in total." % no_m_count

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser(add_help=True, description='Compare the numbers in a list of two files and return which numbers match')
    parser.add_argument("-f", "--first_file", action="store", dest="file1", default=None, help="the first file to compare")
    parser.add_argument("-s", "--second_file", action="store", dest="file2", default=None, help="the second file to compare")
    parser.add_argument("-m", "--match", action="store_true", dest="match", default=None, help="show only matches")
    parser.add_argument("-n", "--no_match", action="store_true", dest="no_match", default=None, help="show only non matches")
    args = parser.parse_args()
    file1 = args.file1
    file2 = args.file2
    match = args.match
    no_match = args.no_match

    number_count(file1, file2, match, no_match)

