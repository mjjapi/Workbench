#!/usr/bin/env python2.7

from datetime import datetime, date, timedelta
import time
import os
import sys
import argparse
import logging as mylog
import csv
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas

class UCBSpreadsheeterCMH():
    """Main class"""

    def __init__(self, workbook, csv_file, save_as, readable):
        self.csv_file = csv_file
        self.workbook = self.open_workbook(workbook)
        self.workbook_name = workbook
        self.save_as = save_as
        self.readable = readable

    def read_csv(self, csv_file):
        """ Read data from a csv file """
        mylog.debug('Reading csv file %s for data' % csv_file)
        csv_data = pandas.read_csv(csv_file)
        mylog.debug('Read of csv file complete.')
        #mylog.debug('%s' % csv_data)
        #sometimes the csv has an empty dataframe  #
        if csv_data.empty:
            mylog.debug('Data frame is empty; repopuating data')
            csv_info = []
            for item in csv_data:
                #add the data one cell at a time to the list #
                #for some reason, some csvs have the data    #
                #with random decimal points                  #
                csv_info.append(item.split(".")[0])
            df = pandas.DataFrame(columns=csv_info)
            df.loc[0]=csv_info
            #write the data from the list back into the cells#
            #one at a time                                   #
            for column in range(0, len(csv_info)):   
                df.iloc[0,column] = csv_info[column]
            csv_data = df 
        return csv_data

    def open_workbook(self, workbook):
        """ Creates the workbook object """
        mylog.debug('Opening workbook %s' % workbook)
        workbook = openpyxl.load_workbook(filename = workbook)
        return workbook

    def load_columns(self, csv_data):
        """Loads the columns from the csv into a list"""
        column_date = []
        column_time = []
        column_hold = []
        column_outcome = []
        for row in dataframe_to_rows(csv_data, index=False):
            cell_date = row[18]
            cell_date = cell_date.split(': ')[1]
            cell_time = row[23]
            cell_hold = row[24]
            cell_outcome = row[25]
            column_date.append(cell_date)
            column_time.append(cell_time)
            column_hold.append(cell_hold)
            column_outcome.append(cell_outcome)
        return column_date, column_time, column_hold, column_outcome 

    def sum_time_cells(self, column_time, column_hold):
        """Add the time of two time cells in seconds"""
        column_sum = []
        for row in range(0, (len(column_time))):
            cell_sum = column_time[row] + column_hold[row]
            column_sum.append(cell_sum)
        return column_sum 

    def convert_time_to_seconds(self, time_value):
        """Take the string value of time and convert to epoch time"""
        time_epoch = []
        mylog.debug('Converting %s to epoch time' % time_value)
        for value in time_value:
            try:
                pattern = ' %I:%M:%S%p'
                time_epoch_mini = int(time.mktime(time.strptime(value, pattern))) 
                time_epoch.append(time_epoch_mini)
            except:
                mylog.debug('%s Does not seem to be in format with leading space' % value)
            try:
                pattern = '%I:%M:%S%p'
                time_epoch_mini = int(time.mktime(time.strptime(value, pattern))) 
                time_epoch.append(time_epoch_mini)
            except:
                mylog.debug('%s Does not appear to be in format without leading space' % value)
        return time_epoch

    def convert_to_seconds(self, time_value):
        time_seconds = []
        mylog.debug('Converting %s to seconds' % time_value)
        for value in time_value:
            try:
                time_formatted = datetime.strptime(value.lstrip(), '%M:%S')
                time_seconds_mini = timedelta(minutes=time_formatted.minute, seconds=time_formatted.second).total_seconds()
                time_seconds.append(int(time_seconds_mini))
            except:
                mylog.debug('%s Does not seem to be in minute:second format' % value)
            try:
                time_formatted = datetime.strptime(value.lstrip(), ':%S')
                time_seconds_mini = timedelta(seconds=time_formatted.second).total_seconds()
                time_seconds.append(int(time_seconds_mini))
            except:
                mylog.debug('%s Does not appear to be in :second format' % value)
        return time_seconds

    def convert_seconds_to_readable(self, time_value):
        """Take a string in epoch and convert to local time"""
        time_readable = []
        for value in time_value:
            time_readable_mini = time.strftime('%I:%M:%S%p', time.localtime(value))
            time_readable.append(time_readable_mini)
            mylog.debug('Converting %s to %s' % (value, time_readable_mini))
        return time_readable

    def convert_outcomes(self, column_outcome):
        """Convert the outcome type to what it is that the client said they wanted"""
        converted_outcomes = []
        mylog.debug('Outcomes to convert: %s' % column_outcome)
        for outcome in column_outcome:
            mylog.debug('Converting outcome: %s' % outcome)
            #if not outcome:
            #if outcome == 'nan':
            if isinstance(outcome, float):
                new_outcome = 'Abandoned'
            elif 'Transfer After Being on Hold' in outcome:
                new_outcome = 'Answered by Rep'
            elif 'Exceeded Max Wait Time' in outcome:
                new_outcome = 'Answered by Voicemail'
            elif 'User Exited Call' in outcome:
                new_outcome = 'Abandoned'
            elif 'No Active Agents in Any Group' in outcome:
                new_outcome = 'Answered by Voicemail'
            mylog.debug('New outcome is %s' % new_outcome)
            converted_outcomes.append(new_outcome)
        return converted_outcomes

    def write_rows(self, sheet, column_date, column_time, column_sum, column_outcome, column_hold, readable):
        if readable:
            header = ['Date of Inbound', 'Time of Inbound', 'Time of Answer or Abandonment', 'Call Outcome', 'Wait Time']
        else:
            header = ['Date of Inbound', 'Time of Inbound', 'Time of Answer or Abandonment', 'Call Outcome', 'Wait Time (sec)']
        sheet.append(header)
        for row in range(0, (len(column_time))):
            mylog.debug('Writing %s %s %s %s %s' % (column_date[row], column_time[row], column_sum[row], column_outcome[row], column_hold[row]))
            cells = [column_date[row], column_time[row], column_sum[row], column_outcome[row], column_hold[row]]
            sheet.append(cells)
        return True

    def Execute(self):
        """Main logic loop"""
        mylog.info('Beginning spreadsheet operations against %s' % self.workbook_name)
        sheet = self.workbook.active
        mylog.info('Loading data from %s' % self.csv_file)
        csv_data = self.read_csv(self.csv_file)
        column_date, column_time, column_hold, column_outcome = self.load_columns(csv_data)
        column_time_epoch = self.convert_time_to_seconds(column_time)
        column_hold_seconds = self.convert_to_seconds(column_hold)
        column_sum = self.sum_time_cells(column_time_epoch, column_hold_seconds)
        column_sum = self.convert_seconds_to_readable(column_sum)
        column_outcome = self.convert_outcomes(column_outcome)
        mylog.debug('Loading data into spreadsheet')
        if not self.readable:
            column_hold = column_hold_seconds
        self.write_rows(sheet, column_date, column_time, column_sum, column_outcome, column_hold, self.readable)
        mylog.info('Saving new spreadsheet')
        if self.save_as:
            self.workbook_name = self.save_as
        self.workbook.save(self.workbook_name)
        mylog.info('Saved as %s' % self.workbook_name)


if __name__ == '__main__':
    #Parse command line arguments
    parser = argparse.ArgumentParser(add_help=True, description='Create or modify the CMH spreadsheet by importing new csv data')
    parser.add_argument("-m", "--monthly", action="store", dest="workbook", default=None, help="aggregate daily data to an existing spreadsheet")
    parser.add_argument("-c", "--csv_source", action="store", dest="csv_source", default=None, help="csv source file to insert into workbook")
    parser.add_argument("-s", "--save_as", action="store", dest="save_as", default=None, help="save the workbook file under a different name")
    parser.add_argument("-d", "--daily", action="store_true", dest="daily", default=False, help="create a spreadsheet with only the day's data based off the daily template")
    parser.add_argument("-r", "--readable", action="store_true", dest="readable", default=False, help="write seconds in M:S format")
    parser.add_argument("--debug", action="store_true", dest="debug", default=False, help="set logging level to output debug messages")

    args = parser.parse_args()
    debug = args.debug

    if debug:
        mylog.basicConfig(stream=sys.stdout, level=mylog.DEBUG, format='%(asctime)s %(levelname)s - %(message)s')
    else:
        mylog.basicConfig(stream=sys.stdout, level=mylog.INFO, format='%(asctime)s %(levelname)s - %(message)s')

    if not args.daily and not args.workbook:
        print "You must supply a monthly workbook upon which to operate."
        sys.exit(1)
    if not args.csv_source:
        print "You must supply a csv to load data from."
        sys.exit(1)
    if args.daily:
        args.workbook = 'Daily_Template.xlsx'
        filedate = time.strftime("%Y-%m-%d")
        args.save_as = 'CMH-Daily-' + filedate + '.xlsx'

    if args.csv_source:
        csv_file = args.csv_source

    ModifySpreadsheet = UCBSpreadsheeterCMH(args.workbook, csv_file, args.save_as, args.readable)

    try:
        ModifySpreadsheet.Execute()
    except SystemExit:
        print "System exit"
        raise
    except KeyboardInterrupt:
        print "Operation cancelled by user interrupt"
        sys.exit(1)
    except:
        print "Unknown exception:"
        raise
        sys.exit(1)

