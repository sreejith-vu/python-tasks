#!/usr/bin/env python
# Description:	This script will go through the schemas specified in the customer.txt and checks whether they are upgraded or not.
#		And sends the status report to mentioned email address.
#		Contents of customer.txt should be in format of - <schema> <build version>
#		Example: nano 12.0.7-8951
# Usage:	./HMSUpgrade_status_report.py

import os
import sys
import subprocess
from datetime import datetime

TABLE = ""
END = "Upgrade end"
BEGIN = "Attempting upgrade"
CMD_HMS_UP_DATE = "date +%F"
CUSTOMER_LIST = "customer.txt"
TYPE = "Content-Type: text/html"
MAIL_TO = "To: svu040@gmail.com"
CMD_LIQUIBASE_DATE = "date +'%d/%m/%Y'"
EMAIL_CONTENT = "/tmp/upgrade_mail.txt"
TODAY_DATE = datetime.now().strftime("%d-%m-%Y")
SUB = "Subject: XXXX Upgradation Status - " + TODAY_DATE
EMAIL_LIST = [['SCHEMA', 'PROPOSED VERSION',
               'INSTALLED VERSION', 'LIQUIBASE', 'UPGRADE STATUS']]
CURR_HMS_VERSION = "head -5 /root/webapps/instahms/WEB-INF/classes/java/resources/application.properties | grep insta.software.version"


def send_mail(EMAIL_LIST):
    global TABLE
    email_content_1 = '''\n<head>\n<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>html title</title>\n<style type="text/css" media="screen">
    table{\nempty-cells:hide;\nfont-family: arial, sans-serif;\nborder: 1px solid black;\ntext-align: center;\nwidth: 70%;\n}
    th.cell{\nborder: 1px solid #5DADE2;\npadding: 8px;\n}
    td.cell{\nborder: 1px solid #dddddd;\npadding: 8px;\n}
    .red {\nbackground-color: #EC7063;\ncolor: black;\npadding: 6px;\n}
    .green {\nbackground-color: #52BE80;\ncolor: black;\npadding: 6px;\n}
    .black {\nbackground-color: #85929E;\ncolor: white;\npadding: 6px;\n}
    </style>\n</head>\n<body>\n<table style="border: blue 1px solid;">'''
    email_content_3 = '''\n</table>\n</body>'''

    for item in EMAIL_LIST:
        if "SCHEMA" in item:
            TABLE += '<tr><th class="cell">' + item[0] + '</td><th class="cell">' + item[1] + '</td><th class="cell">' + \
                item[2] + '</td><th class="cell">' + item[3] + \
                '</td><th class="cell">' + item[4] + '</td></tr>' + '\n'
        if "Found Error" in item[3] and "Upgraded" in item[4]:
            TABLE += '<tr><td class="cell">' + item[0] + '</td><td class="cell">' + item[1] + '</td><td class="cell">' + \
                item[2] + '</td><td class="red">' + item[3] + \
                '</td><td class="green">' + item[4] + '</td></tr>' + '\n'
        if "Found Error" in item[3] and "Not upgraded" in item[4]:
            TABLE += '<tr><td class="cell">' + item[0] + '</td><td class="cell">' + item[1] + '</td><td class="cell">' + \
                item[2] + '</td><td class="red">' + item[3] + \
                '</td><td class="red">' + item[4] + '</td></tr>' + '\n'
        if "No Error" in item[3] and "Upgraded" in item[4]:
            TABLE += '<tr><td class="cell">' + item[0] + '</td><td class="cell">' + item[1] + '</td><td class="cell">' + \
                item[2] + '</td><td class="green">' + item[3] + \
                '</td><td class="green">' + item[4] + '</td></tr>' + '\n'
        if "No Error" in item[3] and "Not upgraded" in item[4]:
            TABLE += '<tr><td class="cell">' + item[0] + '</td><td class="cell">' + item[1] + '</td><td class="cell">' + \
                item[2] + '</td><td class="green">' + item[3] + \
                '</td><td class="red">' + item[4] + '</td></tr>' + '\n'
        if "Not Reachable" in item[3]:
            TABLE += '<tr><td class="cell">' + item[0] + '</td><td class="black">' + item[1] + '</td><td class="black">' + \
                item[2] + '</td><td class="black">' + item[3] + \
                '</td><td class="black">' + item[4] + '</td></tr>' + '\n'

    email_body = MAIL_TO + "\n" + TYPE + "\n" + SUB + "\n\n" + \
        email_content_1 + "\n" + TABLE + email_content_3
    with open(EMAIL_CONTENT, "w") as file:
        file.write(email_body)
        file.close()
    cmd = "sendmail -t < %s" % (EMAIL_CONTENT)
    os.system(cmd)
    print "------------------------------------\nSending Status Report %s" % MAIL_TO
    os.system("echo > " + CUSTOMER_LIST)


def get_data(hostname, proposed_version, current_version, LB_FLAG, upgrade_flag):
    if LB_FLAG == 0:
        liquibase_details = "No Error"
    elif LB_FLAG == 1:
        liquibase_details = "Found Error"
    else:
        liquibase_details = "Not Reachable"

    if upgrade_flag == 0:
        upgrade_status = "Upgraded"
    elif upgrade_flag == 1:
        upgrade_status = "Not upgraded"
    else:
        upgrade_status = "Not Reachable"

    EMAIL_LIST.append([hostname, proposed_version,
                       current_version, liquibase_details, upgrade_status])

    with open(CUSTOMER_LIST) as file:
        lines = file.readlines()
        last_line = lines[-1].split(" ")[0]
        if last_line == hostname:
            send_mail(EMAIL_LIST)


def verify(hostname, proposed_version, current_version, LB_FLAG):
    if current_version == proposed_version:
        print "Version got upgraded successfully"
        upgrade_flag = 0
    else:
        print "Version not upgraded"
        upgrade_flag = 1
    get_data(hostname, proposed_version,
             current_version, LB_FLAG, upgrade_flag)


def liquibase_log(hostname, proposed_version, current_version):
    global LB_FLAG
    LB_FLAG = 0
    try:
        if os.stat(LIQUIBASE_LOG).st_size != 0:
            with open(LIQUIBASE_LOG) as file:
                lines = file.readlines()
            for line in lines:
                if server_date_liquibase in line:
                    if "ERROR" in line:
                        LB_FLAG = 1
        else:
            print "Liquibase log file is empty"
        if LB_FLAG == 1:
            print "Error in Liquibase log"
        else:
            print "No Error in Liquibase log"
    except Exception as e:
        print "Unable to open liquibase log file"

    verify(hostname, proposed_version, current_version, LB_FLAG)


def hms_upgrade(hostname, proposed_version, current_version):
    global UP_FLAG
    UP_FLAG = 0
    try:
        if os.stat(HMS_UP_LOG).st_size != 0:
            with open(HMS_UP_LOG) as file:
                lines = file.readlines()
        else:
            print "Upgrade log is empty"

    except Exception as e:
        print "Unable to open upgrade.log"

    try:
        for line in lines:
            if server_date_hms in line:
                if BEGIN in line:
                    print "Log file got updated, checking further."
                    UPGRADING_VERSION = line.split("to ", 1)[1].strip('\n')
                    print "Upgrading attempt version from hms.log : ", UPGRADING_VERSION
                if END in line:
                    UP_FLAG = 0
                else:
                    UP_FLAG = 1
            else:
                print "Upgrade didn't started"
                UP_FLAG = 1
                break

        if UP_FLAG == 0:
            print "Successfully upgraded"
        else:
            print "Application not upgraded"

    except Exception as e:
        print "pattern error"

    liquibase_log(hostname, proposed_version, current_version)


def ssh_server(hostname, proposed_version):
    global server_date_hms
    global server_date_liquibase
    print "Connecting to : ", hostname
    response = os.system("ping -c 1 " + hostname + " > /dev/null")
    if response == 0:
        print "Connection Successfull"
        try:
            server_date_hms = subprocess.check_output(
                ["ssh", "%s" % hostname, CMD_HMS_UP_DATE], shell=False).strip()
            print "server_date_hms: ", server_date_hms
            CMD_HMS_UP_LOG = "tail -25 /var/log/insta/hms/upgrade.log | head -24 > /tmp/" + \
                hostname+"_upgrade.log"
            HMS_UP_LOG = "/tmp/"+hostname+"_upgrade.log"
            cmd = "ssh %s %s" % (hostname, CMD_HMS_UP_LOG)
            os.system(cmd)
            print "Current server upgrade.log is saved to /tmp/"+hostname+"_upgrade.log"
        except Exception as e:
            print "Error in fetching data from upgrade.log"

        try:
            global current_version
            current_version = subprocess.check_output(
                ["ssh", "%s" % hostname, CURR_HMS_VERSION], shell=False).strip().split("= ")[1]
            print "current_version: ", current_version
        except Exception as e:
            print "Error in fetching current version"

        try:
            server_date_liquibase = subprocess.check_output(
                ["ssh", "%s" % hostname, CMD_LIQUIBASE_DATE], shell=False).strip()
            print "server_date_liquibase: ", server_date_liquibase
            CMD_LIQUIBASE_LOG = "cat /var/log/insta/hms/liquibase.log > /tmp/" + \
                hostname+"_liquibase.log"
            LIQUIBASE_LOG = "/tmp/"+hostname+"_liquibase.log"
            cmd = "ssh %s %s" % (hostname, CMD_LIQUIBASE_LOG)
            os.system(cmd)
            print "Current server liquibase.log is saved to /tmp/test_liquibase.log"
        except Exception as e:
            print "Error in fetching data from liquibase.log"

        hms_upgrade(hostname, proposed_version, current_version)

    else:
        print "Server Not Reachable"
        proposed_version = "Not Reachable"
        current_version = "Not Reachable"
        LB_FLAG = "Not Reachable"
        upgrade_flag = "Not Reachable"
        get_data(hostname, proposed_version,
                 current_version, LB_FLAG, upgrade_flag)


def main():
    try:
        global proposed_version
        if os.stat(CUSTOMER_LIST).st_size != 0:
            with open(CUSTOMER_LIST) as file:
                lines = file.readlines()
                print "Reading from customer.txt"
        else:
            print "Found empty file %s, exiting." % CUSTOMER_LIST
            sys.exit(2)
    except Exception as e:
        print "%s not found, exiting." % CUSTOMER_LIST
        sys.exit(2)

    try:
        for line in lines:
            hostname = line.split(" ", 1)[0]
            proposed_version = line.split(" ", 1)[1].strip('\n')
            print "------------------------------------"
            print "Customer/Schema is : ", hostname
            print "Proposed version is : ", proposed_version
            ssh_server(hostname, proposed_version)
    except Exception as e:
        print e
        print "Error in reading from %s.\nIt should be in below format seperated by single space:\n\n\tschema 12.0.7.8855\n\n" % CUSTOMER_LIST
        sys.exit(2)


if __name__ == "__main__":
    main()
