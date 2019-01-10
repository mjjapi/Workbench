#!/usr/bin/env python2.7
"""
Composed Dec 2018 by Absolute Performance, INC
For questions send email to:
csteam@absolute-performance.com
*Ensure the path to db2 is defined in cron
TO DO: 
"""

import ibm_db
import subprocess
import sys
import os
import logging as mylog
from datetime import datetime
import time

class LoadTables():

    def __init__(self, database, host, port, user, password, schema, db_config, cache_directory, sql_file_path, db2_path, keep):
        self.database = database
        self.host = host
        self.port = port
        self.user = user
        self.password = password
	self.schema = schema
        self.config_directory = db_config.rstrip('/')
        self.cache_directory = cache_directory.rstrip('/')
        self.sql_file_path = sql_file_path.rstrip('/')
	self.keep = keep
	self.db2_path = db2_path
        if password:
            self.cred2 = password
        else:
            self.cred2 = ''
        if user:
            self.cred1 = user
        else:
            self.cred1 = 'batchusr'

    def connect_db(self, database, host, port, user, password):
        connection_string = ("DATABASE={0};" "HOSTNAME={1};" "PORT={2};" "PROTOCOL=TCPIP;" "UID={3};" "PWD={4};").format(database, host, port, user, password)
        mylog.debug("Connection string = %s" % connection_string)
        try:
            connection = ibm_db.connect(connection_string, '','')
        except:
            mylog.critical("Unable to establish connection with database %s with parameters host:%s port:%s user:%s password:%s protocol:TCPIP" % (database, host, port, user, password))
            print "Unable to establish connection with database %s with parameters host:%s port:%s user:%s password:%s protocol:TCPIP" % (database, host, port, user, password)
            sys.exit(1)
        return connection

    def get_timestamp(self):
	timestamp = str(datetime.now().strftime('%Y%m%d-%H%M%S-%f')[:-3])
	return timestamp 

    def check_load_pending(self, table):
	load_pend = False
	mylog.debug('Checking if %s is in load pending state' % table)
	schema = table.split('.')[0].strip()
	table_name = table.split('.')[1].strip()
	command = "select status from syscat.tables where tabschema='" + schema + "' and tabname='" + table_name +"'"
	command_obj = self.execute_command(command)
	result = self.get_result(command_obj)
	mylog.debug('Returned status for %s is: %s' % (table, result))
	try:
	    if 'C' in result[0]['STATUS']:
	        mylog.warning('LOAD PEND state discovered for table %s' % table)
	        load_pend = True
	    elif 'X' in result[0]['STATUS']:
	        mylog.error('Table %s is INOPERATIVE' % table)
	    elif 'N' in result[0]['STATUS']:
	        mylog.debug('Table is OK')
	    else:
	        mylog.warning('Table state is undefined:' % result)
	except:
	    mylog.warning('Unknown return to check load pending command, skipping: %s' % result)
        return load_pend


    def execute_command(self, command):
        mylog.debug("Executing command: %s" % command)
        try:
            execute_return = ibm_db.exec_immediate(self.connection, command)
        except:
            mylog.critical("Unable to execute command: %s" % command)
            result = ibm_db.stmt_errormsg()
            mylog.critical("Command return was: %s" % result)
            print "PROCESS ERROR: Failed to execute command %s; command return was %s" % (command, result)
            execute_return = result
        return execute_return

    def execute_sql(self, sql_file):
        mylog.debug("Executing SQL file %s" % sql_file)
	now_time = self.get_timestamp()
	output_file = sql_file.split('.')[0] + '-' + now_time + '.OUT'
	mylog.debug('SQL DB2 output file: %s' % output_file)
	db2_param = 'db2' + ' -tvxz ' + output_file + ' -f'
	total_command = db2_param  + ' ' + sql_file 
	mylog.debug('Command to execute sql file is: %s' % total_command)
        proc = subprocess.Popen(total_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, errors = proc.communicate()
        return out, errors

    def write_sql_file(self, sql_file, lines):
        mylog.debug('Writing to file %s' % sql_file)
        with open(sql_file, 'a') as new_file:
            for line in lines:
                mylog.debug('Writing line: %s' % line)
                new_file.write(line + '\n')
	os.chmod(sql_file, 0o777)
        return True

    def delete_sql_files(self, sql_file_path, sql_files):
        for ffile in sql_files:
            if not '.sql' in ffile:
                ffile = ffile + '.sql'
            ffile_path = sql_file_path + '/' + ffile
            mylog.debug('Deleting file %s' % (ffile_path))
            proc = subprocess.Popen(['rm', '-r', ffile_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, errors = proc.communicate()
            if errors:
                mylog.error('Unable to delete %s with ERROR %s' % (ffile_path, errors))
            else:
                mylog.debug('%s' % out)
        if errors:
            return False
        else:
            return True

    def get_list_of_sql_files(self, sql_file_path):
        final_list = []
        mylog.debug('Fetching list of current sql files')
        file_list = os.listdir(sql_file_path)
        for ffile in file_list:
            if '.sql' in ffile:
                final_list.append(ffile)
        return final_list

    def get_tables(self, tables_file):
        mylog.debug("Fetching tables to load from file %s" % tables_file)
        tables = []
        with open(tables_file, "r") as table_list:
            for line in table_list:
                tables.append(line.strip())
        return tables

    def table_difference(self, file_list, table_list):
        file_table_list = []
        delete = False
        mylog.debug('Comparing %s to %s' % (file_list, table_list))
        for table in file_list:
            file_table_list.append(table.split('.sql')[0])
        diff = list(set(table_list) - set(file_table_list))
        if diff:
            mylog.debug('New sql files to be written are %s' % diff)
        else:
            mylog.debug('No new sql files to be written. Checking if any are to be deleted')
        del_diff = list(set(file_table_list) - set(table_list))
        if del_diff:
            mylog.debug('sql files to be deleted are %s' % diff)
            delete = del_diff
        else:
            mylog.debug('No sql files to be deleted.')
        if not diff:
            mylog.debug('There is no difference in files or tables this execution')
        return diff, delete

    def get_result(self, command):
        result = []
	skip = False
        mylog.debug("Fetching return for command: %s" % command)
        try:
            if 'SQLSTATE=' in command:
                mylog.error('Result to parse contains SQL error code; skipping')
                result = command
		skip = True
        except:
            mylog.debug('%s is ibm_db object' % command)

	if not skip:
	    try:
                ret = ibm_db.fetch_assoc(command)
	    except:
	        mylog.warning('Unable to parse return from command: %s' % command)
	        ret = None
	    if ret:
                while ret:
                    result.append(ret)
                    ret = ibm_db.fetch_assoc(command)
        return result

    def compose_sql_file(self, schema, table, source, sql_file_path):
        sql_lines = []
        header = 'connect to ' + self.database + ' user ' + self.cred1 + ' USING ' + self.cred2 + ';'
        commit = 'COMMIT;'
        terminate = 'TERMINATE;'
        sql_file = sql_file_path + '/' + schema + '.' + table + '.sql'

        """DECLARE"""
        mylog.debug('===========================')
        mylog.debug("Loading SCHEMA %s for table: %s" % (schema, table))
        declare_sql = "DECLARE " + schema + "_" + table + "_CURSOR cursor DATABASE " + source + " user  USING  for SELECT * from " + schema + "." + table + " with ur;"
        mylog.debug("%s" % declare_sql)

        """LOAD"""
        load_sql = "LOAD from " + schema + "_" + table + "_CURSOR of cursor SAVECOUNT 1000 MESSAGES " + self.cache_directory + "/" + schema + "." + table + ".msg REPLACE into " + schema + "." + table + " nonrecoverable;"
        """ One table in iipuid01, iipuid04  and iipuid05 is special """
        if table == 'PARTY' and schema == 'TIGCOM':
            load_sql = "LOAD from " + schema + "_" + table + "_CURSOR of cursor MODIFIED BY generatedoverride SAVECOUNT 1000 MESSAGES " + self.cache_directory + "/" + schema + "." + table + ".msg REPLACE into " + schema + "." + table + " nonrecoverable;"
        """ Some tables in iins02 and iins05 are special """
        if table == 'BALACC' and schema == 'IIS':
            load_sql = "LOAD from " + schema + "_" + table + "_CURSOR of cursor MODIFIED BY identityignore SAVECOUNT 1000 MESSAGES " + self.cache_directory + "/" + schema + "." + table + ".msg REPLACE into " + schema + "." + table + " nonrecoverable;"
        if table == 'BALACC' and schema == 'WCSIFB':
            load_sql = "LOAD from " + schema + "_" + table + "_CURSOR of cursor MODIFIED BY identityoverride SAVECOUNT 1000 MESSAGES " + self.cache_directory + "/" + schema + "." + table + ".msg REPLACE into " + schema + "." + table + " nonrecoverable;"
        if table == 'DOCTRG':
            load_sql = "LOAD from " + schema + "_" + table + "_CURSOR of cursor MODIFIED BY identityoverride SAVECOUNT 1000 MESSAGES " + self.cache_directory + "/" + schema + "." + table + ".msg REPLACE into " + schema + "." + table + " nonrecoverable;"
        if table == 'REQEST':
            load_sql = "LOAD from " + schema + "_" + table + "_CURSOR of cursor MODIFIED BY identityignore SAVECOUNT 1000 MESSAGES " + self.cache_directory + "/" + schema + "." + table + ".msg REPLACE into " + schema + "." + table + " nonrecoverable;"
        mylog.debug("%s" % load_sql)

        """SET INTEGRITY"""
        set_int_sql = "SET INTEGRITY FOR " + schema + "." + table + " STAGING, MATERIALIZED QUERY, FOREIGN KEY, GENERATED COLUMN, CHECK FULL ACCESS IMMEDIATE UNCHECKED;"
        mylog.debug("%s" % set_int_sql)

        """RUNSTATS"""
        runstats_sql = "runstats on table " + schema + "." + table + " on all columns with distribution and indexes all allow write access;"
        mylog.debug("%s" % runstats_sql)

        sql_lines.append(header)
        sql_lines.append(declare_sql)
        sql_lines.append(load_sql)
        sql_lines.append(set_int_sql)
        sql_lines.append(runstats_sql)
        sql_lines.append(commit)
        sql_lines.append(terminate)
        mylog.debug('.sql file lines: %s' % sql_lines)
        self.write_sql_file(sql_file, sql_lines)
        mylog.debug('===========================')
        return True

    def alter_sequence(self, table, schema, generate_id):
	check = False
        errors = []
        table_added = False
        mylog.debug("Running ALTER SEQUENCE on table %s" % table)
        if generate_id:
            max_pk_sql = "SELECT MAX(" + table + "ID) from " + schema + "." + table + " with ur"
        else:
            max_pk_sql = "SELECT MAX(ID) from " + schema + "." + table + " with ur"
        mylog.debug("%s" % max_pk_sql)
        max_pk = self.execute_command(max_pk_sql)
        max_pk_result = self.get_result(max_pk)
        if 'SQLSTATE=' in max_pk_result:
            mylog.error('SQL ERROR for table %s' % table)
            errors.append(table)
            table_added = True
            errors.append(max_pk_result)
        else:
            mylog.debug('MAX_PK return: %s' % max_pk_result)
            check = self.check_max_pk(max_pk_result)
        if check:
            max_pk = check + 1
            alter_seq_sql = "alter sequence  " + schema + "." + table + "_SEQ restart with " + str(max_pk)
            mylog.debug("%s" % alter_seq_sql)
            execute_alter_max_pk = self.execute_command(alter_seq_sql)

	    """ALTER SEQUENCE command return isn't parseable by ibm_db, but the command can still """
	    """execute properly.  Wrap with Try and nullify result if there is an error when """
	    """parsing output """
            alt_result = self.get_result(execute_alter_max_pk)
            if 'SQLSTATE=' in alt_result:
                mylog.error('SQL ERROR for table %s' % table)
                if not table_added:
                    errors.append(table)
		    table_added = True
                errors.append(alt_result)
            else:
	    	"""If there is no SQL ERROR from ALT SEQ command, verify ALT SEQ command executed successfully """
		mylog.debug('Verifying ALTER SQUENCE command executed')
		alt_check_sql = "select next value for " + schema + "." + table + "_SEQ from ( values 1 )"
		alt_check = self.execute_command(alt_check_sql)
		alt_check_result = self.get_result(alt_check)
		if 'SQLSTATE=' in alt_check_result:
		    mylog.error('SQL ERROR for table %s' % table)
		    if not table_added:
			errors.append(table)
			table_added = True
		    errors.append(alt_check_result)
		else:
		    mylog.debug('Verification return: %s' % alt_check_result)
		new_alt_seq = self.check_max_pk(alt_check_result)
		if new_alt_seq:
		    if new_alt_seq == max_pk:
			mylog.debug('New sequence successfully implemented')
			check_ok = True
		    else:
			check_ok = False
			mylog.error('ERROR - new sequence not successfully implemented; see error log for details')
		else:
		    mylog.error('ERROR - new sequence is not an integer; see error log for details')
	            mylog.error('ERROR for table %s' % table)
		    if not table_added:
			errors.append(table)
		    alt_seq_error = 'ALTER SEQUENCE command against table ' + table + ' failed.  New sequence returned non-integer value.'
		    errors.append(alt_seq_error)
        else:
            mylog.debug("MAX_PK is not integer; skipping")
        return errors

    def check_max_pk(self, max_pk_result):
	try:
            max_pk = max_pk_result[0]['1']
            mylog.debug("Checking to see if the MAX_PK value of %s is an integer" % max_pk)
	except:
	    max_px_int = None
	try:
	    max_pk_int = int(max_pk)
            mylog.debug("MAX_PK value is integer: %s" % max_pk_int)
	except:
	    max_pk_int = None
            mylog.debug("MAX_PK value is not integer")
        return max_pk_int 

    def delete_from_transid(self, schema, table, transid_1, transid_2):
        errors = []
        mylog.debug("Executing special tansaction delete command for %s.%s" % (schema, table))
        delete_sql = "delete from " + schema + "." + table + " WHERE TRANSID BETWEEN " + transid_1 + " AND " + transid_2 + ";"
        execute_delete = self.execute_command(delete_sql)
        result = self.get_result(execute_delete)
        if 'SQLSTATE=' in result:
            mylog.error('SQL ERROR for table %s' % table)
            errors.append(table)
            errors.append(result)
        else:
            mylog.debug('DELETE return: %s' % result)
        return errors

    def iipuid_special_table_max_id(self, table):
        """Inherited from RESET_MAXID-IIPUID01-small.ksh """
        errors = []
	last_part = None
        mylog.debug("This stored procedure will return an error code if the tables are empty")
        if table == 'DELETEME':
            last_part = "('TIGCOM','DELETEME')"
        if table == 'LITEXPANDATA2':
            last_part = "('POLC','LITEXPANDATA2')"
	if last_part:
            sql = "CALL BATCHUSR.RESTARTMAXID" + last_part
            execute_special = self.execute_command(sql)
	    result = self.get_result(execute_special)
            if 'SQLSTATE=' in result:
                mylog.error('SQL ERROR for table %s' % table)
                errors.append(table)
                errors.append(result)
            return errors
	else:
	    return False

    def iins_special_table_max_id(self, table):
        errors = []
	table_name = table.split('.')[1].strip()
	table_schema = table.split('.')[0].strip()
        mylog.debug("This stored procedure will return an error code if the tables are empty")
        sql = "CALL BATCHUSR.RESTARTMAXID('" + table_schema + "','" + table_name + "')"
        execute_special = self.execute_command(sql)
	result = self.get_result(execute_special)
        if 'SQLSTATE=' in result:
            mylog.error('SQL ERROR for table %s' % table)
            errors.append(table)
            errors.append(result)
        return errors

    def iipuid_special_table_alt_seq(self):
        """This table must be atered separately because of the format by which its """
        """MAX_PK is called """
        errors = []
	table = 'TIGCOM.BUSINESSTRANSACTION'
        table_added = False
        max_pk_sql = "select MAX(TRANSID) from TIGCOM.BUSINESSTRANSACTION with ur"
        mylog.debug("%s" % max_pk_sql)
        max_pk = self.execute_command(max_pk_sql)
	max_pk_result = self.get_result(max_pk)
        if 'SQLSTATE=' in max_pk_result:
            mylog.error('SQL ERROR for table %s' % table)
            errors.append(table)
            table_added = True
            errors.append(max_pk_result)
        else:
            mylog.debug('MAX_PK return: %s' % max_pk_result)
        max_pk = int(max_pk_result[0]['1']) + 1
        alter_seq_sql = "alter sequence TIGCOM.BUSINESSTRANSACTION_SEQ restart with " + str(max_pk)
        mylog.debug("%s" % alter_seq_sql)
        execute_alter_max_pk = self.execute_command(alter_seq_sql)
	alt_result = self.get_result(execute_alter_max_pk)
        if 'SQLSTATE=' in alt_result:
            mylog.error('SQL ERROR for table %s' % table)
            if not table_added:
                errors.append(table)
            errors.append(alt_result)
        else:
            mylog.debug('ALTER SEQUENCE return: %s' % alt_result)
        return errors

    def iipuid_execute(self):
        if not self.host:
	    if self.database == 'iipuid05' or self.database == 'IIPUID05':
	        self.host = '192.168.1.43'
	    if self.database == 'iipuid01' or self.database == 'IIPUID01' or self.database == 'iipuid03' or self.database == 'IIPUID03':
                self.host = '192.168.1.45'
	    if self.database == 'iipuid04' or self.database == 'IIPUID04':
                self.host = '192.168.1.47'
        if not self.port:
            self.port = '60010'
        mylog.debug('database:%s host:%s port:%s user:%s password:<masked>' % (self.database, self.host, self.port, self.cred1))
        self.connection = self.connect_db(self.database, self.host, self.port, self.cred1, self.cred2)
        iipuid_errors = {}
        load_pend = []
	load_pend_cleared = 0
	if self.database == 'iipuid01' or self.database == 'IIPUID01':
            tables_file = self.config_directory + '/IIPUID01.config'
            alt_seq_list_1 = self.config_directory + '/IIPUID01_ALT_SEQ_FIND_MAXID.config'
            alt_seq_list_2 = self.config_directory + '/IIPUID01_ALT_SEQ_NO_MAX.config'
	if self.database == 'iipuid05' or self.database == 'IIPUID05':
	    tables_file = self.config_directory + '/IIPUID05.config'
	    alt_seq_list_1 = None
	    alt_seq_list_2 = self.config_directory + '/IIPUID05_ALT_SEQ_NO_MAX.config'
        if self.database == 'iipuid04' or self.database == 'IIPUID04':
            tables_file = self.config_directory + '/IIPUID04.config'
            alt_seq_list_1 = None
            alt_seq_list_2 = self.config_directory + '/IIPUID04_ALT_SEQ_NO_MAX.config'
        if self.database == 'iipuid03' or self.database == 'IIPUID03':
            tables_file = self.config_directory + '/IIPUID03.config'
            alt_seq_list_1 = self.config_directory + '/IIPUID03_ALT_SEQ_FIND_MAXID.config'
            alt_seq_list_2 = self.config_directory + '/IIPUID03_ALT_SEQ_NO_MAX.config'

	mylog.info("Identified config files are: %s, %s, %s" % (tables_file, alt_seq_list_1, alt_seq_list_2))
        source = 'MRPUID06'
        mylog.info("Fetching table list for %s" % self.database)
        table_list = self.get_tables(tables_file)
        """Check to see if sql file already exists"""
        mylog.info('Comparing list to current sql files')
        sql_files = self.get_list_of_sql_files(self.sql_file_path)
        diff, delete = self.table_difference(sql_files, table_list)
        if delete:
            ran_ok = self.delete_sql_files(self.sql_file_path, delete)
            if not ran_ok:
                mylog.warning('Some files were not deleted - their respective tables will still be executed against')
        if diff:
            for new_file in diff:
                table_name = new_file.split('.')[1].strip()
                table_schema = new_file.split('.')[0].strip()
                self.compose_sql_file(table_schema, table_name, source, self.sql_file_path)
        mylog.info("Processing tables")
        """Begin processing tables"""
#        sql_file_list = self.get_list_of_sql_files(self.sql_file_path)
	tables_list = self.get_tables(tables_file)
        for table_file in tables_list:
#        for table_file in sql_file_list:
            table = table_file
            """Execute .sql files"""
	    table_file_path = self.sql_file_path + '/' + table_file + '.sql'
            out, errors = self.execute_sql(table_file_path)
	    mylog.debug('SQL execution output: %s; %s' % (out, errors))
            if 'SQLSTATE=' in out or 'SQLSTATE=' in errors:
	        mylog.error('Errors found in executing %s' % table_file)
                iipuid_errors[table] = errors 
            else:
                mylog.debug('.sql file %s successfully executed' % table_file)
	"""Check for Load Pending State"""
        for table_file in tables_list:
#        for table_file in sql_file_list:
            table = table_file            
	    table_file_path = self.sql_file_path + '/' + table_file + '.sql'
	    load_pend_check = self.check_load_pending(table)
            if load_pend_check:
                mylog.warning('LOAD PENDING state detected, reloading .sql for %s' % table)
                retry = 5
                while retry:
                    retry_out, retry_errors = self.execute_sql(table_file_path)
                    if 'SQLSTATE=' in retry_errors or 'SQLSTATE=' in retry_out:
                        mylog.error('Errors found in executing %s' % table_file)
                        iipuid_errors[table] = retry_errors
                    retry_load_pend_check = self.check_load_pending(table)
                    if retry_load_pend_check:
                        mylog.warning('Still detecting LOAD PENDING state; sleep for 5 seconds before trying again')
                        retry = retry - 1
			time.sleep(5)
                    else:
                        mylog.debug('LOAD PENDING state has CLEARED')
                        retry = 0
                        cleared_string = table + ': CLEARED LOAD PEND'
			load_pend_cleared = load_pend_cleared + 1
                        load_pend.append(cleared_string)
                last_load_pend_check = self.check_load_pending(table)
                if last_load_pend_check:
                    mylog.warning('Still detecting LOAD PENDING state. Marking table %s' % table)
                    load_pend.append(table)
        """Alter Sequence"""
        mylog.info('Fetching ALT SEQ tables for %s' % self.database)
        mylog.info("Processing tables")
	"""Special table set 1"""
	if not alt_seq_list_1:
	    alter_errors = self.iipuid_special_table_max_id(alt_seq_list_2)
	else:
            alt_seq_tables = self.get_tables(alt_seq_list_1) + self.get_tables(alt_seq_list_2)
            alter_errors = self.iipuid_special_table_max_id(alt_seq_tables)
        if alter_errors:
            iipuid_errors[alter_errors[0]] = alter_errors[1]
	"""Special table set 2"""
        alter_errors = self.iipuid_special_table_alt_seq()
        if alter_errors:
            error_count = len(alter_errors) - 1
            for i in error_count:
                iipuid_errors[alter_errors[0]] = alter_errors[i]
	if alt_seq_list_1:
            alt_seq_tables_1 = self.get_tables(alt_seq_list_1)
            for seq_table in alt_seq_tables_1:
	        """General table set 1"""
	        mylog.debug('Operating on table: %s' % seq_table)
                table_name = seq_table.split('.')[1].strip()
                table_schema = seq_table.split('.')[0].strip()
                alter_errors = self.alter_sequence(table_name, table_schema, True)
                if alter_errors:
                    for i in range(0, len(alter_errors)):
                        iipuid_errors[alter_errors[0]] = alter_errors[i]
	if alt_seq_list_2:
            alt_seq_tables_2 = self.get_tables(alt_seq_list_2)
            for seq_table in alt_seq_tables_2:
	        """General table set 2"""
	        mylog.debug('Operating on table: %s' % seq_table)
                table_name = seq_table.split('.')[1].strip()
                table_schema = seq_table.split('.')[0].strip()
                alter_errors = self.alter_sequence(table_name, table_schema, False)
                if alter_errors:
                    for i in range(0, len(alter_errors)):
                        iipuid_errors[alter_errors[0]] = alter_errors[i]
	mylog.info("Completed process for %s" % self.database)
        mylog.info("Errors encountered in this process:")
        for key, value in sorted(iipuid_errors.items()):
            mylog.info("%s: %s" % (key, value))
	ld_pnd_cnt = len(load_pend)
        mylog.info("Tables detected to be in Load Pending state during load: %s" % ld_pnd_cnt)
        mylog.info("Tables detected to have cleared Load Pending state: %s" % load_pend_cleared)
	for pended_table in load_pend:
            mylog.info("%s" % pended_table)
	if not self.keep:
	    mylog.info("Deleting .msg files")
	    msg_files_command = 'rm -f ' + self.cache_directory + '/*.msg'
	    proc = subprocess.Popen(msg_files_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	    rm_out, rm_errors = proc.communicate()
	    if rm_errors:
	        mylog.debug('Deleted %s with errors %s' % (rm_out, rm_errors))
	    else:
		mylog.debug('Deleted %s' % rm_out)
	    mylog.info("Deleting .OUT files")
	    out_files_command = 'rm -f ' + self.config_directory + '/*.OUT'
	    proc = subprocess.Popen(out_files_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	    rmout_out, rmout_errors = proc.communicate()
	    if rmout_errors:
		mylog.debug('Deleted %s with errors %s' % (rmout_out, rmout_errors))
	    else:
	        mylog.debug('Deleted %s' % rmout_out)
        mylog.info("Sending status email")
	if self.database == 'iipuid05' or self.database == 'IIPUID05':
           email_cmd = subprocess.Popen('/db2/db2home/db2clmsi/SCRIPTS/checkLoadPending.sh db2clmsi iipuid05', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	if self.database == 'iipuid04' or self.database == 'IIPUID04':
           email_cmd = subprocess.Popen('/db2/db2home/db2clmqi/SCRIPTS/checkLoadPending.sh db2clmqi iipuid04', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	if self.database == 'iipuid01' or self.database == 'IIPUID01' or self.database == 'IIPUID03' or self.database == 'iipuid03':
            email_cmd = subprocess.Popen('/db2/db2home/db2clmdi/SCRIPTS/checkLoadPending.sh db2clmdi iipuid01', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        email_output = email_cmd.communicate()[0]
        mylog.info('%s' % email_output)

    def iins_execute(self):
        if not self.host:
            if self.database == 'iins02' or self.database == 'IINS02' or self.database == 'iins03' or self.database == 'IINS03':
                self.host = '192.168.1.45'
            if self.database == 'iins05' or self.database == 'IINS05':
                self.host = '192.168.1.43'
            if self.database == 'iins04' or self.database == 'IINS04':
                self.host = '192.168.1.47'
        if not self.port:
            self.port = '60010'
        mylog.debug('database:%s host:%s port:%s user:%s password:<masked>' % (self.database, self.host, self.port, self.cred1))
        self.connection = self.connect_db(self.database, self.host, self.port, self.cred1, self.cred2)	
        iins_errors = {}
        load_pend = []
	load_pend_cleared = 0
        special_already_executed = False
	if self.database == 'iins02' or self.database == 'IINS02':
	    tables_file = self.config_directory + '/IINS02.config'
            alt_seq_list_1 = self.config_directory + '/IINS02_ALT_SEQ_FIND_MAXID.config'
            alt_seq_list_2 = self.config_directory + '/IINS02_ALT_SEQ_NO_MAX.config'
            maxid_list = self.config_directory + '/IINS02_RESTART_MAXID.config'
	    emlref_script = self.config_directory + '/UPDATE_EMLREF.script'
        if self.database == 'iins03' or self.database == 'IINS03':
            tables_file = self.config_directory + '/IINS03.config'
            alt_seq_list_1 = self.config_directory + '/IINS03_ALT_SEQ_FIND_MAXID.config'
            alt_seq_list_2 = self.config_directory + '/IINS03_ALT_SEQ_NO_MAX.config'
            maxid_list = self.config_directory + '/IINS03_RESTART_MAXID.config'
            emlref_script = self.config_directory + '/UPDATE_EMLREF.script'
        if self.database == 'iins04' or self.database == 'IINS04':
            tables_file = self.config_directory + '/IINS04.config'
            alt_seq_list_1 = self.config_directory + '/IINS04_ALT_SEQ_FIND_MAXID.config'
            alt_seq_list_2 = self.config_directory + '/IINS04_ALT_SEQ_NO_MAX.config'
            maxid_list = self.config_directory + '/IINS04_RESTART_MAXID.config'
            emlref_script = self.config_directory + '/UPDATE_EMLREF.script'
        if self.database == 'iins05' or self.database == 'IINS05':
	    tables_file = self.config_directory + '/IINS05.config'
            alt_seq_list_1 = self.config_directory + '/IINS05_ALT_SEQ_FIND_MAXID.config'
            alt_seq_list_2 = self.config_directory + '/IINS05_ALT_SEQ_NO_MAX.config'
            maxid_list = self.config_directory + '/IINS05_RESTART_MAXID.config'
	    emlref_script = self.config_directory + '/UPDATE_EMLREF.script'
        source = 'MRIINS06'
        mylog.info("Fetching table list for %s" % self.database)
        table_list = self.get_tables(tables_file)
        """Check to see if sql file already exists"""
        mylog.info('Comparing list to current sql files')
        sql_files = self.get_list_of_sql_files(self.sql_file_path)
        diff, delete = self.table_difference(sql_files, table_list)
        if delete:
            ran_ok = self.delete_sql_files(self.sql_file_path, delete)
            if not ran_ok:
                mylog.warning('Some files were not deleted - their respective tables will still be executed against')
        if diff:
            for new_file in diff:
                table_name = new_file.split('.')[1].strip()
                table_schema = new_file.split('.')[0].strip()
                self.compose_sql_file(table_schema, table_name, source, self.sql_file_path)
        mylog.info("Processing tables")
        """Begin processing tables"""
#        sql_file_list = self.get_list_of_sql_files(self.sql_file_path)
	tables_list = self.get_tables(tables_file)
	"""Special delete execution"""
	self.delete_from_transid('TIGCOM', 'BUSINESSTRANSACTION', '600000000', '699000000')
	"""Main table load loop"""
        for table_file in tables_list:
#        for table_file in sql_file_list:
            table = table_file
            """Execute .sql files"""
            table_file_path = self.sql_file_path + '/' + table_file + '.sql'
#            table_file_path = self.sql_file_path + '/' + table_file
            out, errors = self.execute_sql(table_file_path)
            mylog.debug('SQL execution output: %s; %s' % (out, errors))
            if 'SQLSTATE=' in out or 'SQLSTATE=' in errors:
                mylog.error('Errors found in executing %s' % table_file)
                iins_errors[table] = errors
            else:
                mylog.debug('.sql file %s successfully executed' % table_file)
        """Check for Load Pending State"""
        for table_file in tables_list:
#        for table_file in sql_file_list:
            table = table_file
            table_file_path = self.sql_file_path + '/' + table_file + '.sql'
            load_pend_check = self.check_load_pending(table)
            if load_pend_check:
                mylog.warning('LOAD PENDING state detected, reloading .sql for %s' % table)
                retry = 5
                while retry:
                    retry_out, retry_errors = self.execute_sql(table_file_path)
                    if 'SQLSTATE=' in retry_errors or 'SQLSTATE=' in retry_out:
                        mylog.error('Errors found in executing %s' % table_file)
                        iins_errors[table] = retry_errors
                    retry_load_pend_check = self.check_load_pending(table)
                    if retry_load_pend_check:
                        mylog.warning('Still detecting LOAD PENDING state; sleep for 5 seconds before trying again')
                        retry = retry - 1
                        time.sleep(5)
                    else:
                        mylog.debug('LOAD PENDING state has CLEARED')
                        retry = 0
                        cleared_string = table + ': CLEARED LOAD PEND'
			load_pend_cleared = load_pend_cleared + 1
                        load_pend.append(cleared_string)
                last_load_pend_check = self.check_load_pending(table)
                if last_load_pend_check:
                    mylog.warning('Still detecting LOAD PENDING state. Marking table %s' % table)
                    load_pend.append(table)
        """Alter Sequence"""
        if not special_already_executed:
            iins_maxid_table = self.get_tables(maxid_list)
            for l_table in iins_maxid_table:
                special_errors = self.iins_special_table_max_id(l_table)
                if special_errors:
                    iins_errors[special_errors[0]] = special_errors[1]
            special_already_executed = True
        alt_seq_tables_1 = self.get_tables(alt_seq_list_1)
        for seq_table in alt_seq_tables_1:
            table_name = seq_table.split('.')[1].strip()
            table_schema = seq_table.split('.')[0].strip()
            alter_errors = self.alter_sequence(table_name, table_schema, True)
            if alter_errors:
                error_count = len(alter_errors) - 1
                for i in error_count:
                    iins_errors[alter_errors[0]] = alter_errors[i]
        alt_seq_tables_2 = self.get_tables(alt_seq_list_2)
        for seq_table in alt_seq_tables_2:
            table_name = seq_table.split('.')[1].strip()
            table_schema = seq_table.split('.')[0].strip()
            alter_errors = self.alter_sequence(table_name, table_schema, False)
            if alter_errors:
                error_count = len(alter_errors) - 1
                for i in error_count:
                    iins_errors[alter_errors[0]] = alter_errors[i]
	"""Update EMLREF script execute"""
	mylog.debug('Executing EMLREF script for %s' % self.database)
        emlref_out, emlref_errors = self.execute_sql(emlref_script)	
        if 'SQLSTATE=' in emlref_errors or 'SQLSTATE=' in emlref_out:
            mylog.error('Errors found in executing %s' % emlref_script)
            iins_errors['EMLREF'] = emlref_out
        mylog.info("Completed process for %s" % self.database)
        mylog.info("Errors encountered in this process:")
        for key, value in sorted(iins_errors.items()):
            mylog.info("%s: %s" % (key, value))
	ld_pnd_cnt = len(load_pend)
        mylog.info("Tables detected to be in Load Pending state during load: %s" % ld_pnd_cnt)
        mylog.info("Tables detected to have cleared Load Pending state: %s" % load_pend_cleared)
        for pended_table in load_pend:
            mylog.info("%s" % pended_table)
        if not self.keep:
            mylog.info("Deleting .msg files")
            msg_files_command = 'rm -f ' + self.cache_directory + '/*.msg'
            proc = subprocess.Popen(msg_files_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            rm_out, rm_errors = proc.communicate()
            if rm_errors:
                mylog.debug('Deleted %s with errors %s' % (rm_out, rm_errors))
            else:
                mylog.debug('Deleted %s' % rm_out)
            mylog.info("Deleting .OUT files")
            out_files_command = 'rm -f ' + self.config_directory + '/*.OUT'
            proc = subprocess.Popen(out_files_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            rmout_out, rmout_errors = proc.communicate()
            if rmout_errors:
                mylog.debug('Deleted %s with errors %s' % (rmout_out, rmout_errors))
            else:
                mylog.debug('Deleted %s' % rmout_out)
        mylog.info("Sending status email")
	if self.database == 'iins02' or self.database == 'IINS02' or self.database == 'iins03' or self.database == 'IINS03':
            email_cmd = subprocess.Popen('/db2/db2home/db2clmdi/SCRIPTS/checkLoadPending.sh db2clmdi iins02', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	if self.database == 'iins05' or self.database == 'IINS05':
            email_cmd = subprocess.Popen('/db2/db2home/db2clmsi/SCRIPTS/checkLoadPending.sh db2clmsi iins05', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	if self.database == 'iins04' or self.database == 'IINS04':
            email_cmd = subprocess.Popen('/db2/db2home/db2clmqi/SCRIPTS/checkLoadPending.sh db2clmqi iins04', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        email_output = email_cmd.communicate()[0]
        mylog.info('%s' % email_output)


    def Execute(self):
        mylog.info("Beginning table loads for %s" % self.database)
        if self.database == "IIPUID01" or self.database == "iipuid01" or self.database == "IIPUID05" or self.database == "iipuid05" or self.database == "IIPUID04" or self.database == "iipuid04" or self.database == "IIPUID03" or self.database == "iipuid03":
            self.iipuid_execute()
	elif self.database == "IINS02" or self.database == "iins02" or self.database == "IINS05" or self.database == "iins05" or self.database == "IINS03" or self.database == "iins03" or self.database == "iins04" or self.database == "IINS04":
	    self.iins_execute()
        else:
            mylog.info("A process for %s is not supported at this time" % self.database)
            sys.exit(1)
            """
            mylog.info("Connecting to %s" % self.database)
            table_list = self.get_tables(self.db_config)
            mylog.info("Loading table schemas")
            for table in table_list:
				self.schema_load(table)
				self.set_integrity(table)
				self.runstats(table)
				self.alter_sequence(table, self.schema)
            """
        mylog.info("Completed process for %s" % self.database)
	mylog.info("\n\n\n")


if __name__ == '__main__':
    import argparse
    #Parse command line arguments
    parser = argparse.ArgumentParser(add_help=True, description='Process table loads into the specified database; you MUST specify a database upon which to operate; specify a parameter for host, port, user, password or schema if you do not wish to use the default for that database')
    parser.add_argument("-d", "--database", action="store", dest="database", default=None, help="database name to connect to")
    parser.add_argument("-i", "--host_id", action="store", dest="host", default=None, help="database host name or IP address")
    parser.add_argument("-p", "--port", action="store", dest="port", default=None, help="correct port to connehct through")
    parser.add_argument("-u", "--user", action="store", dest="user", default=None, help="username for database")
    parser.add_argument("-x", "--xword", action="store", dest="xword", default=None, help="username password")
    parser.add_argument("-s", "--schema", action="store", dest="schema", default=None, help="database schema")
    parser.add_argument("-c", "--config_directory", action="store", dest="db_config", default=None, help="directory in which the config files are stored")
    parser.add_argument("-m", "--msg_directory", action="store", dest="cache_directory", default=None, help="directory in which to store .msg files; if one is not specified, the curent directory will be used")
    parser.add_argument("-f", "--sql_file_directory", action="store", dest="sql_file_path", default=None, help="directory in which the .sql files are located; if one is not specified, the current directory will be used")
    parser.add_argument("-k", "--keep_msg", action="store_true", dest="keep", default=False, help="retain generated .msg files")
    parser.add_argument("--debug", action="store_true", dest="debug", default=False, help="display debug messages")
    parser.add_argument("--test", action="store_true", dest="test", default=False, help="display current path and parameters")
    parser.add_argument("--automate", action="store_true", dest="auto", default=False, help="if executing script from automation, sends email notification on script failure")

    args = parser.parse_args()
    debug = args.debug
    run_path = os.getcwd()
    db2_arg = 'which db2'
    db2_path = subprocess.Popen(db2_arg, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    db2_path_o, db2_path_e = db2_path.communicate()

    if args.test:
	who_am_i_c = subprocess.Popen('whoami',stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	who_am_i, waie = who_am_i_c.communicate()
	print "I am: " + who_am_i
        print "db2 path: " + db2_path_o
	print "Executing directory: " + run_path + "\n"
	print "Parameters: ", args
	print "\n"
	sys.exit(0)
    if debug:
        mylog.basicConfig(stream=sys.stdout, level=mylog.DEBUG, format='%(asctime)s %(levelname)s - %(message)s')
    else:
        mylog.basicConfig(stream=sys.stdout, level=mylog.INFO, format='%(asctime)s %(levelname)s - %(message)s')
    if not args.database:
        print "You must provide a database upon which to operate."
        sys.exit(1)
    if not args.db_config:
        mylog.info('No .config file path specified.  Using current directory')
        mylog.warning('No .config file path specified.  Using current directory')
        args.db_config = run_path 
    if not args.sql_file_path:
        mylog.info('No .sql file path specified.  Using current directory')
        mylog.error('No .sql file path specified.  Using current directory')
        args.sql_file_path = run_path 
    if not args.cache_directory:
        mylog.info('No .msg cache directory specified. Using current directory')
        mylog.critical('No .msg cache directory specified. Using current directory')
        args.cache_directory = run_path

    Load_Tables = LoadTables(args.database, args.host, args.port, args.user, args.xword, args.schema, args.db_config, args.cache_directory, args.sql_file_path, db2_path_o, args.keep)
    try:
        Load_Tables.Execute()
    except SystemExit:
        print "SystemExit exception"
        raise
    except KeyboardInterrupt:
        print "Cancelled by user"
        sys.exit(1)
    except:
        print "Undefined exception"
	if args.auto:
	    email_cmd = subprocess.Popen('/db2/db2home/db2clmsi/SCRIPTS/table_load_failure.sh', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	    email_output = email_cmd.communicate()[0]
            print '%s' % email_output
        sys.exit(1)
        raise
