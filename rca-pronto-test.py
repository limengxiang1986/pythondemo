import sys
reload(sys)
sys.setdefaultencoding("utf-8")
#from datetime import datetime
import datetime
from flask import Flask,session, request, flash, url_for, redirect, render_template, \
    abort ,g,send_from_directory,jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
#from wtforms import StringField, PasswordField, BooleanField, SubmitField
import mysql.connector
from email.mime.text import MIMEText
from email.header import Header
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.utils import parseaddr,formataddr
import smtplib,time,os

from httplib2 import socks
import socket
from jira.client import JIRA
import requests
#from requests_ntlm import HttpNtlmAuth
#from requests.auth import HTTPBasicAuth
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.runtime.client_request import ClientRequest
from office365.runtime.utilities.request_options import RequestOptions
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.file import File
#import wget
import urllib2

from office365.sharepoint.file_creation_information import FileCreationInformation
import codecs
from os.path import basename
import shutil
import ldap

from rcatrackingconfig import FC_addr_dict,addr_dict1,getjira,JiraRequest,gAdmin, gAuth,teams,jiraRequest1
# from rcatrackingconfig import Todo,TodoAP,Rca5Why,TodoLongCycleTimeRCA,TodoJiraRcaPreparedQualityRating,SystemLog,JiraTodo,\
# InChargeGroup,JiraUser

from fddrcatracking import getDisplayNameByEmailName,FindProductLine,FindCustomerName,FindCustomerNameAB
from fddrcatracking import addToJiraTodo,addTodo,addTodoOnly#,getGroupInChargeInfo
from fddrcatracking import getEmailNameByDisplayName,getBusinessLineAndProductLine
from config import PriorityDict,SourceListDict,BusinessUnitDict,BusinessLineDict,ProductLineDict,CustomerNameDict
from config import AnalysisIssueCaseType,ChildIssueType
from config import RcaCauseType,ChildRootCauseCategory,EdaCauseType,ChildEscapeCauseCategory
from config import RcaActionType,EdaActionType,JiraSubTaskCaseType,JiraChildIssueType
from config import CuDoBusinessLineDict,CuDoProductLineDict,CuDoCustomerNameDict

import json
import threading
import urllib3


"""
PROXY_TYPE_HTTP=3
socks.setdefaultproxy(3,"10.144.1.10",8080)
socket.socket = socks.socksocket
"""

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@mysql-rca-shark:3306/fddrca?charset=utf8'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@10.157.5.174:31402/fddrca?charset=utf8'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://lmx:12345678@localhost:3306/blog?charset=utf8'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = 'secret_key'
app.config['DEBUG'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_RECYCLE'] = 299
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 20

db = SQLAlchemy(app)


def MnRcaEdaCheckAndAssign(jira):
    print 'Starting MnRcaEdaCheckAndAssignment...'
    # edaTaskCreationPerConfigurationTime(jira)


    todos = MnTodo.query.filter_by(JiraTaskIsCreated='No',JIRAProject='MNRCA' \
                                   # ,PRID='02324733'
                                   ).all()
    # PRID='CAS-199145-Q5P9'
    # todos = MnTodo.query.filter(MnTodo.PRID=='CAS-296907-H3B9').all()
    for todo_item in todos:
        PRID = todo_item.PRID
        PRAttached = todo_item.PRAttached
        # InChargeGroupName = todo_item.PRGroupInCharge
        JIRAProject = todo_item.JIRAProject

        if checkLocalExisting(PRID,PRAttached):
            todo_item = MnTodo.query.get(PRID)
            todo_item.JiraTaskIsCreated = 'Yes'
            db.session.commit()
            continue

        if JIRAProject == 'MNRCA':
            PRSeverity = todo_item.PRSeverity.strip()
            InChargeGroupName = todo_item.PRGroupInCharge.strip()
            FaRcaEdaDecisionFlag = todo_item.FaRcaEdaDecisionFlag
            PRClosedDate = todo_item.PRClosedDate
            # FaRcaEdaStatus = getFaRcaEdaStatus(PRID)
            if FaRcaEdaDecisionFlag == 'Yes' and PRClosedDate >= '2019-01-01':
            # if FaRcaEdaStatus == False and PRClosedDate >= '2019-01-01':
                FaCreateAndAssign(jira, PRID, PRAttached)
                continue
            if todo_item.PRClosedDate < '2019-01-01':
                todo_item = MnTodo.query.get(PRID)
                todo_item.JiraTaskIsCreated = 'Yes'
                db.session.commit()
                continue
            # BusinessLine = todo_item.BusinessLine
            # ProductLine = todo_item.ProductLine
            inchargegroupinfo = getGroupInChargeInfo(PRID, InChargeGroupName)
            if inchargegroupinfo:
                RCAFilter = inchargegroupinfo.RCAFilter
                CaseType = inchargegroupinfo.RCAEDACategory.strip()
                EdaCaseType = inchargegroupinfo.EdaCaseType
                JiraIssueAssignee = inchargegroupinfo.AssessorEmail.strip()
            else:
                continue
            if PRSeverity == 'C - Minor' and RCAFilter != 'All Customer(A+B+C), All Internal' and \
                    RCAFilter != 'All Customer(A+B+C), No Internal':
                continue
            customer = isCustomer(PRID)
            if customer == False and RCAFilter != 'All Customer(A+B+C), All Internal':
                continue
            else:
                exceptionFlag,existingFlag = checkJiraExistingDiff(jira,PRID,PRAttached)
                if exceptionFlag:
                    continue
                if exceptionFlag == False and existingFlag:
                # if checkJiraExisting(jira, PRID, PRAttached):
                    todo_item = MnTodo.query.get(PRID)
                    todo_item.JiraTaskIsCreated = 'Yes'
                    db.session.commit()
                    continue
                CaseType = 'RCA'
                JiraIssueAssignee = ''
                CaseType = inchargegroupinfo.RCAEDACategory.strip()
                EdaCaseType = inchargegroupinfo.EdaCaseType
                EDA_AssessorEmail = inchargegroupinfo.EDA_AssessorEmail
                if EDA_AssessorEmail:
                    EDA_AssessorEmail = EDA_AssessorEmail.strip()
                EDACreatingTime = inchargegroupinfo.EDACreatingTime
                # if EDACreatingTime == 'Together With RCA':
                #     EDA_JiraIssueAssignee = getAccountIdByEmailName(EDA_AssessorEmail)
                JiraIssueAssignee = inchargegroupinfo.AssessorEmail.strip()
                if JiraIssueAssignee == 'enqing.lei@nokia-sbell.com':
                    # teamAssessor = getTeamAssessorEmail(PRID)
                    teamAssessor = getTeamAssessorEmailnew(PRID)
                    if teamAssessor:
                        JiraIssueAssignee = teamAssessor
                    # else:
                    #     JiraIssueAssignee = 'qinyu.zhao@nokia-sbell.com'
                print 'JiraIssueAssignee=%s PRID= %s'%(JiraIssueAssignee,PRID)
                AssigneeEmail = JiraIssueAssignee
                JiraIssueAssignee = getAccountIdByEmailName(JiraIssueAssignee)
                AddedBy = inchargegroupinfo.AddedBy
                # watcher = getAccountIdByEmailName(AddedBy)
                reporter = getAccountIdByEmailName(AddedBy)
                if reporter == '':
                    reporter = 'rcashark'
                watcher = reporter
                operation_status,issue = createParent5WhyRcaTaskFirst(jira,PRID)
                if operation_status == False:
                    continue
                    # return
                # issue = jira.issue('MNRCA-22768')
                RcaAnalysisSubtaskKey = issue.key
                ProntoInfo = issue.fields.summary

                summaryinfo = '%s for ' % CaseType + PRID

                rcaDueDate = (datetime.datetime.now() + datetime.timedelta(days=15)).strftime("%Y-%m-%d")
                dueDate = (datetime.datetime.now() + datetime.timedelta(days=15)).strftime(
                    "%Y-%m-%dT%H:%M:00.00+0200")
                JiraIssueProductLine = todo_item.ProductLine
                # reporter = watcher
                if JiraIssueProductLine == 'TD LTE' or AddedBy == 'enqing.lei@nokia-sbell.com':
                    reporter = 'bqgk83'
                if JiraIssueProductLine == 'FDD LTE':
                    reporter = 'vdh483'
                if AddedBy == 'vladimir.nazarkin@nokia.com' and \
                        todo_item.PRProduct.strip() == 'Flexi Multiradio BTS SingleRAN':
                    # reporter = 'wro02917'
                    reporter = 'vdh483'
                if todo_item.PRRcaEdaAssessor == 'piotr.laskowski@nokia.com' or \
                        AddedBy == 'piotr.laskowski@nokia.com':
                    if todo_item.PRProduct.strip() != 'Flexi Multiradio BTS SingleRAN':
                        reporter = 'pilaskow'
                    else:
                        # reporter = 'wro02917'
                        reporter = 'vdh483'

                if CaseType == 'RCA' or CaseType == 'RCA and EDA':
                    CaseType = AnalysisIssueCaseType[CaseType]
                    issueaddforRCAsubtask = {
                        'project': {'id': u'41675'},
                        'parent': {"key": RcaAnalysisSubtaskKey},
                        'issuetype': {'id': u'19800'},  # Analysis subtask
                        'summary': summaryinfo,
                        'customfield_10464': {'id': CaseType},  # Case Type
                        'customfield_27792': dueDate,
                        # 'assignee': {'name': JiraIssueAssignee},
                        'reporter': {'name': reporter},
                        # 'watcher': {'name': watcher},
                    }
                    newissue = jira.create_issue(issueaddforRCAsubtask)
                    try:
                        jira.assign_issue(newissue, JiraIssueAssignee)
                    except:
                        pass
                    jira.remove_watcher(newissue, 'qmxh38')
                    try:
                        jira.add_watcher(newissue, watcher)
                    except:
                        pass
                    url = "https://pronto.inside.nsn.com/prontoapi/rest/api/latest/problemReport/%s" %PRID
                    r = requests.get(url, verify=False, auth=('krma', 'Nokia123'))
                    todo_item1 = MnTodo.query.get(PRID)
                    todo_item1.JiraTaskIsCreated = 'Yes'
                    db.session.commit()
                    # try:
                    #     addTodo(PRID, newissue.key, AssigneeEmail, r, rcaDueDate)
                    # except:
                    #     pass
                    # addToJiraTodo(newissue, PRID)
                    # MnRcaMetricsUpdateNew(newissue,jira)
                    MnRcaMetricsUpdateWithAssignee(AssigneeEmail, newissue, jira)
                    continue
                if EdaCaseType=='EDA':
                    EDA_AssessorEmail = inchargegroupinfo.EDA_AssessorEmail.strip()
                    EDACreatingTime = inchargegroupinfo.EDACreatingTime.strip()
                    CaseType = AnalysisIssueCaseType[EdaCaseType]
                    summaryinfo = '%s for ' % EdaCaseType + PRID
                    edaDueDate = (datetime.datetime.now() + datetime.timedelta(days=45)).strftime("%Y-%m-%d")
                    dueDate = (datetime.datetime.now() + datetime.timedelta(days=45)).strftime(
                        "%Y-%m-%dT%H:%M:00.00+0200")
                    if EDACreatingTime == 'Together With RCA':
                        JiraIssueAssignee = getAccountIdByEmailName(EDA_AssessorEmail)
                        issueaddforRCAsubtask = {
                            'project': {'id': u'41675'},
                            'parent': {"key": RcaAnalysisSubtaskKey},
                            'issuetype': {'id': u'19800'},  # Analysis subtask
                            'summary': summaryinfo,
                            'customfield_10464': {'id': CaseType},  # Case Type
                            'customfield_27792': dueDate,
                            # 'assignee': {'name': JiraIssueAssignee},
                            'reporter': {'name': reporter},
                            # 'watcher': {'name': watcher},
                        }
                        newissue = jira.create_issue(issueaddforRCAsubtask)
                        try:
                            jira.assign_issue(newissue, JiraIssueAssignee)
                        except:
                            pass
                        jira.remove_watcher(newissue, 'qmxh38')
                        jira.add_watcher(newissue, watcher)
                        # todo_item1 = Todo.query.get(PRID)
                        # if todo_item1:
                        #     todo_item1.EdaJiraIssueAssignee = EDA_AssessorEmail
                        #     todo_item1.EdaSubtaskJiraId = newissue.key
                        #     todo_item1.edaDueDate = edaDueDate
                        #     todo_item1.EdaJiraIssueStatus = str(newissue.fields.status)
                        #     db.session.commit()
                        db.session.commit()
                        updateEdaInfo(PRID, newissue, EDA_AssessorEmail, edaDueDate)
                        # addToJiraTodo(newissue, PRID)
                        # MnRcaMetricsUpdateNew(newissue,jira)
                        MnRcaMetricsUpdateWithAssignee(EDA_AssessorEmail, newissue, jira)


def isCustomer(PRID):
    url = "https://pronto.inside.nsn.com/prontoapi/rest/api/latest/problemReport/%s" % PRID
    r = requests.get(url, verify=False, auth=(gAdmin, gAuth))
    a = r.json()
    customer = False
    author = a['author']
    if author == 'Electra':
        customer = True
    return customer


def checkJiraExistingDiff(jira,PRID,AttachedPRID):
    exceptionFlag = False
    existingFlag = False
    PRID = '"' + PRID + '"'
    try:
        issues = jira.search_issues(jql_str='project = MNPRCA AND summary~' + PRID + ' AND type = "5WhyRCA" ',maxResults=5)
    except:
        exceptionFlag = True
        return exceptionFlag,False
    if issues:
        existingFlag = True  # Parent issue exist.
        return exceptionFlag,existingFlag
    if AttachedPRID:
        attachedList = AttachedPRID.split(',')
        for PRID in attachedList:
            PRID = '"' + PRID + '"'
            try:
                issues = jira.search_issues(jql_str='project = MNPRCA AND summary~' + PRID + ' AND type = "5WhyRCA" ',                               maxResults=5)
            except:
                exceptionFlag = True
                return exceptionFlag,False
            if issues:
                existingFlag = True  # Parent issue exist.
                return False,existingFlag
    return exceptionFlag,existingFlag


def createParent5WhyRcaTaskFirst(jira,PRID):
    PRID1 = '"' + PRID + '"'
    issues = jira.search_issues(jql_str='project = MNPRCA AND summary~' + PRID1 + ' AND type = "5WhyRCA" ',maxResults=5)
    if issues:
       return False,''
    todo_item = MnTodo.query.get(PRID)
    PRAttached = todo_item.PRAttached
    PRSeverity = todo_item.PRSeverity
    CustomerName = todo_item.CustomerName
    JiraIssuePriority = 'Major'
    PRSeverity = PRSeverity.split()
    if len(PRSeverity) >= 3:
        JiraIssuePriority = PRSeverity[2]
    if JiraIssuePriority in PriorityDict.values():
        new_dict = {v: k for k, v in PriorityDict.items()}
        JiraIssuePriority = new_dict[JiraIssuePriority]
    # JiraIssueSourceList = 'NCDR'
    ReportedBy = todo_item.ReportedBy  # Customer or Nokia,Vendor,Collaborator
    if ReportedBy == 'Customer' and CustomerName != 'Nokia':
        JiraIssueSourceList = 'NCDR'
    # elif ReportedBy == 'Nokia' and todo_item.FaRcaEdaDecisionFlag == 'Yes':
    elif todo_item.FaRcaEdaDecisionFlag == 'Yes':
        JiraIssueSourceList = 'Internal R & D improvement'
    else:
        JiraIssueSourceList ='Lessons learned'
    if JiraIssueSourceList in SourceListDict.values():
        new_dict = {v: k for k, v in SourceListDict.items()}
        JiraIssueSourceList = new_dict[JiraIssueSourceList]
    JiraIssueBusinessUnit = todo_item.BusinessUnit
    if JiraIssueBusinessUnit in BusinessUnitDict.values():
        new_dict = {v: k for k, v in BusinessUnitDict.items()}
        JiraIssueBusinessUnit = new_dict[JiraIssueBusinessUnit]
    JiraIssueBusinessLine = todo_item.BusinessLine
    JiraIssueProductLine = todo_item.ProductLine
    InChargeGroupName = todo_item.PRGroupInCharge
    # # inchargegroupinfo = InChargeGroup.query.get(InChargeGroupName)
    # inchargegroupinfo = InChargeGroup.query.filter_by(InChargeGroupName=InChargeGroupName, \
    #                                                  BusinessLine=JiraIssueBusinessLine,
    #                                                  ProductLine='All').first()
    # if not inchargegroupinfo:
    #     inchargegroupinfo = InChargeGroup.query.filter_by(InChargeGroupName=InChargeGroupName, \
    #                                                      BusinessLine=JiraIssueBusinessLine,
    #                                                      ProductLine=JiraIssueProductLine).first()
    # if not inchargegroupinfo:
    #     inchargegroupinfo = InChargeGroup.query.filter_by(InChargeGroupName=InChargeGroupName, \
    #                                                      AddedBy='sufang.huang@nokia-sbell.com').first()
    inchargegroupinfo = getGroupInChargeInfo(PRID, InChargeGroupName)
    if inchargegroupinfo:
        AddedBy = inchargegroupinfo.AddedBy
    # if todo_item.PRRcaEdaAssessor =='piotr.laskowski@nokia.com' and \
    #         todo_item.ProductLine.strip() == 'SRAN/SBTS':
    if todo_item.PRRcaEdaAssessor == 'piotr.laskowski@nokia.com' or \
            AddedBy == 'piotr.laskowski@nokia.com':
        if todo_item.ProductLine.strip() == 'SRAN/SBTS':
            JiraIssueBusinessLine = 'SRAN'
    if todo_item.ProductLine.strip() == 'WBTS':
        JiraIssueBusinessLine = 'SRAN'
    if JiraIssueBusinessLine in BusinessLineDict.values():
        new_dict = {v: k for k, v in BusinessLineDict.items()}
        JiraIssueBusinessLine = new_dict[JiraIssueBusinessLine]
    JiraIssueProductLine = todo_item.ProductLine
    if JiraIssueProductLine in ProductLineDict.values():
        new_dict = {v: k for k, v in ProductLineDict.items()}
        JiraIssueProductLine = new_dict[JiraIssueProductLine]

    JiraIssueCustomerName = todo_item.JiraCustomerName
    if JiraIssueCustomerName in CustomerNameDict.values():
        new_dict = {v: k for k, v in CustomerNameDict.items()}
        JiraIssueCustomerName = new_dict[JiraIssueCustomerName]
    else:
        JiraIssueCustomerName = '-1'
    JiraIssueFeatureComponent = ''
    JiraIssueOther = ''
    JiraIssueLabels = ''.strip().split()
    # InChargeGroupName = todo_item.PRGroupInCharge
    # inchargegroupinfo = InChargeGroup.query.get(InChargeGroupName)
    if inchargegroupinfo:
        Labels = inchargegroupinfo.Labels
        JiraIssueLabels = Labels.strip().split()
    PRTitle = todo_item.PRTitle
    PRTitle = strip_non_ascii(PRTitle)
    PRRelease = todo_item.PRRelease
    try:
        sharepoint_status,link = upload_sharepoint(PRID)
    except:
        link = ''
        sharepoint_status = False
        pass
    if sharepoint_status == False:
        return False,''
    prontolink = "https://pronto.int.net.nokia.com/pronto/problemReport.html?prid={0}".format(PRID)
    analysislink = str(link)
    # print PRID
    # print analysislink
    Prontonumber = PRID + ' ' + PRAttached
    Prontonumber = tools_strip(Prontonumber)
    summaryinfo = PRID + ':' + PRTitle
    if len(summaryinfo) > 255:
        summaryinfo = summaryinfo[0:255]
    JiraIssueAssignee = ''
    fourtyFiveDaysLater = (datetime.datetime.now() + datetime.timedelta(days=45)).strftime("%Y-%m-%d")
    # dict1 = {'customfield_38090': fourtyFiveDaysLater}
    AddedBy = inchargegroupinfo.AddedBy
    reporter = getAccountIdByEmailName(AddedBy)
    if reporter == '':
        reporter = 'rcashark'
    if todo_item.ProductLine == 'TD LTE' or AddedBy == 'enqing.lei@nokia-sbell.com':
        reporter = 'bqgk83'
    if todo_item.ProductLine == 'FDD LTE':
        reporter = 'vdh483'
    if AddedBy == 'vladimir.nazarkin@nokia.com' and \
            todo_item.PRProduct.strip() == 'Flexi Multiradio BTS SingleRAN':
        # reporter = 'wro02917'
        reporter = 'vdh483'
    if todo_item.PRRcaEdaAssessor =='piotr.laskowski@nokia.com' or \
            AddedBy == 'piotr.laskowski@nokia.com':
        if todo_item.PRProduct.strip() != 'Flexi Multiradio BTS SingleRAN':
            reporter = 'pilaskow'
        else:
            # reporter = 'wro02917'
            reporter = 'vdh483'
            # return # Donnot serve Wieszczeczynski, Przemyslaw (Nokia - PL/Wroclaw) ,his is not polite
    issueaddforRCAsubtask = {
        'project': {'id': u'41675'},
        'issuetype': {'id': u'17678'},
        'summary': summaryinfo,
        'customfield_37060': Prontonumber,
        'customfield_37069': {'id': JiraIssueSourceList},  # Source List u'206960'
        'customfield_37460': {'id': JiraIssueBusinessUnit},  # Business Unit{}
        'customfield_37061': [{'id': JiraIssueBusinessLine}],  # 'Business Linef{}',
        'customfield_37062': {'id': JiraIssueProductLine},  # {'Product Line'},
        'customfield_37063': JiraIssueFeatureComponent,  # 'Feature Component'
        'customfield_37015': prontolink,
        'priority': {'id': JiraIssuePriority},
        'labels': JiraIssueLabels,  # ['AAA', 'BBB'],
        'customfield_37059': PRRelease,  # 'Release Fault Introduced', #softwareRelease
        'customfield_32006': [{'id': JiraIssueCustomerName}],  # {'Customer':}, # less[
        'customfield_38068': JiraIssueOther,  # {Other} #More filled CMCC
        'customfield_37064': analysislink,
        # 'customfield_38090': fourtyFiveDaysLater,
        'assignee': {'name': JiraIssueAssignee},
        'reporter': {'name': reporter}
    }
    # print 'InChargeGroupName: %s ,Reporter is: %s !!!!!!'%(InChargeGroupName,reporter)
    newissue = jira.create_issue(issueaddforRCAsubtask)
    jira.remove_watcher(newissue, 'qmxh38')
    return True,newissue


def tools_strip(str):
    if str == None:
        return ""
    return str.strip(",").strip(" ")


def strip_non_ascii(string):
    ''' Returns the string without non ASCII characters'''
    stripped = (c for c in string if 0 < ord(c) < 127)
    return ''.join(stripped)


def getTeamAssessorEmailnew(PRID):
    url = "https://pronto.inside.nsn.com/prontoapi/rest/api/latest/problemReport/%s" % PRID
    try:
        r = requests.get(url, verify=False, auth=(gAdmin, gAuth))
    except:
        return ''
    a = r.json()
    PRGroupInCharge = a['groupIncharge']
    correctionIds = a['correctionIds']
    for correctionId in correctionIds:
        urlcf = "https://pronto.inside.nsn.com/prontoapi/rest/api/latest/correction/%s" % correctionId
        r = requests.get(urlcf, verify=False, auth=(gAdmin, gAuth))
        try:
            b = r.json()
        except:
            return ''
        responsiblePerson = b['correctionModification'][0]['responsiblePerson']
        implementationGroup = b['correctionModification'][0]['implementationGroup']
        if PRGroupInCharge != implementationGroup:
            continue
        respList = resp_members(responsiblePerson)
        for item in respList:
            fixerEmailAddress = getEmailNameByDisplayName(item)
            lineEmailAddress = getLineManagerEmailName(fixerEmailAddress)
            # if b['state'] == 'Tested':
            squadGroupAssessorInfo = SquadGroupAssessor.query.filter_by(assessorSquadGroupLead=lineEmailAddress).\
                order_by(SquadGroupAssessor.assessorId.desc()).first()
            if squadGroupAssessorInfo:
                assessorEmailAddress = squadGroupAssessorInfo.squadGroupRcaEdaAssessor
                return assessorEmailAddress
            else:
                # if lineEmailAddress in addr_dict1.keys():
                #     if addr_dict1[lineEmailAddress] in FC_addr_dict.keys():
                #         lineName = addr_dict1[lineEmailAddress]
                #         assessorEmailAddress = FC_addr_dict[lineName]['fc']
                #         if lineEmailAddress == 'mingjing.liu@nokia-sbell.com':
                #             continue
                #         else:
                #             return assessorEmailAddress
                # else:
                print 'No find in HZ in Tested CR PRID= %s except mingjing team'% PRID
                assessorEmailAddress = fixerEmailAddress
                return assessorEmailAddress
    return '' # No find valid CR in HZ


def upload_sharepoint(PRID):
    basedir = os.path.abspath(os.path.dirname(__file__))
    # SHAREPOINT_COMMON_USER = 'enqing.lei@nokia.com'
    # SHAREPOINT_COMMON_PWD = 'kkcqqgfmmxkgjjmd'
    # # SHAREPOINT_COMMON_USER = 'nsn-intra\qmxh38'
    # SHAREPOINT_COMMON_PWD = 'Happy@2019'
    SHAREPOINT_COMMON_USER = 'kpiautomation.rma@nokia.com'
    SHAREPOINT_COMMON_PWD = 'gxfgsqcwnhrjfnzr'
    site_url ='https://nokia.sharepoint.com/sites/LTERCA/'
    ctx_auth = AuthenticationContext(site_url)
    # print "Authenticate credentials"
    if ctx_auth.acquire_token_for_user(SHAREPOINT_COMMON_USER, SHAREPOINT_COMMON_PWD):
        ctx = ClientContext(site_url, ctx_auth)
        options = RequestOptions(site_url)
        ctx_auth.authenticate_request(options)
        ctx.ensure_form_digest(options)
        path = get_5whyrca_template(PRID)
        link = upload_binary_file(path,ctx_auth)
        return True,link
    else:
        return False,ctx_auth.get_last_error()


def get_5whyrca_template(PRID):
    file_dir = os.path.join(basedir, '5WhyRcaTemplate')
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    # templatefilename = 'RCA_EDA_Analysis_Template_LTE_BL-mode.xlsm'
    templatefilename = 'RCA_EDA_Analysis_Template_LTE_BL-mode.xlsx'
    #fullpatholdtemplatefilename = 'D://01-TMT/00-Formal RCA/'+ templatefilename
    fullpatholdtemplatefilename = os.path.join(file_dir, templatefilename)
    #fullpatholdtemplatefilename = 'D:\\01-TMT\\00-Formal RCA' + templatefilename
    # filename = PRID + '.xlsm'
    filename = PRID + '.xlsx'
    fullpathnewtemplatefilename = os.path.join(file_dir, filename)
    shutil.copyfile(fullpatholdtemplatefilename, fullpathnewtemplatefilename)
    return fullpathnewtemplatefilename


def upload_binary_file(file_path, ctx_auth):
    """Attempt to upload a binary file to SharePoint"""
    base_url = 'https://nokia.sharepoint.com/sites/LTERCA/'
    folder_url = "RcaStore"
    file_name = basename(file_path)
    files_url ="{0}/_api/web/GetFolderByServerRelativeUrl('{1}')/Files/add(url='{2}', overwrite=true)"
    full_url = files_url.format(base_url, folder_url, file_name)
    file_link = "{0}/_api/web/GetFileByServerRelativePath('{1}')/Files/add(url='{2}', overwrite=true)"
    file_link1 = "{0}/_api/web/GetFileByServerRelativePath(decodedurl='/sites/LTERCA/RcaStore/{1}')"
    # https: // nokia.sharepoint.com / sites / LTERCA / _api / web / GetFileByServerRelativePath(
    #     decodedurl='/sites/LTERCA/RcaStore/CAS-49425-C8L1.xlsm')

    file_full_link = file_link.format(base_url, folder_url, file_name)
    file_full_link1 = file_link1.format(base_url, file_name)


    options = RequestOptions(base_url)
    context = ClientContext(base_url, ctx_auth)
    context.request_form_digest()

    options.set_header('Accept', 'application/json; odata=verbose')
    options.set_header('Content-Type', 'application/octet-stream')
    options.set_header('Content-Length', str(os.path.getsize(file_path)))
    options.set_header('X-RequestDigest', context.contextWebInformation.form_digest_value)
    options.method = 'POST'

    with open(file_path, 'rb') as outfile:

        # instead of executing the query directly, we'll try to go around
        # and set the json data explicitly

        context.authenticate_request(options)

        data = requests.post(url=full_url, data=outfile, headers=options.headers, auth=options.auth)

        if data.status_code == 200:
            # our file has uploaded successfully
            # let's return the URL
            base_site = data.json()['d']['Properties']['__deferred']['uri'].split("/sites")[0]
            link = data.json()['d']['LinkingUrl']
            relative_url = data.json()['d']['ServerRelativeUrl'].replace(' ', '%20')
            #LinkingUri
            #return base_site + relative_url
            return link
        else:
            # data = requests.get(url= file_full_link1,headers=options.headers, auth=options.auth)
            # link = data.json()['d']['LinkingUrl']
            return ''
            # return data.json()['error']


def resp_members(b):
    members = []
    #b = 'Ma, Cong 2. (NSB - CN/Hangzhou),Ma, Cong 3. (NSB - CN/Hangzhou),'
    if b:
        a=b.split('),')
        #c=a[0]+')'
        n=len(a)
        if n>1:
            for i in range(n-1):
                c = a[i] + ')'
                members.append(c.encode('utf-8').strip())
            members.append(a[n-1].encode('utf-8').strip())
        else:
            members.append(b.encode('utf-8').strip())
        return members
        print a
    else:
        return members

def get_ldap_connection():
    # conn = ldap.initialize(app.config['LDAP_PROVIDER_URL'])
    try:
        conn = ldap.initialize('ldap://ed-p-gl.emea.nsn-net.net')
        conn.simple_bind_s('cn=BOOTMAN_Acc,ou=SystemUsers,ou=Accounts,o=NSN', 'Eq4ZVLXqMbKbD4th')
    except:
        return ''

    return conn

def getLineManagerEmailName(JiraIssueAssignee):
    AssignTo = JiraIssueAssignee.strip()
    # user = JiraUser.query.filter_by(email=AssignTo).first()
    # if user:
    #     lineManagerEmail = user.lineManagerEmail
    # else:
    try:
        conn = get_ldap_connection()
    except:
        print 'ldap connection error!!!'
        AssignTo =''
        return AssignTo
    filter = '(mail=%s)' % AssignTo
    attrs = ['sn', 'mail', 'cn', 'displayName', 'nsnManagerAccountName']
    base_dn = 'o=NSN'
    # conn = app.config['ldap']
    try:
        result = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)
    except:
        print 'No such account!!!'
        print 'getLineManagerEmailName, No such account!!! mail = %s *******' % AssignTo
        AssignTo =''
        return AssignTo
    if result:
        lineManagerAccountId = result[0][1]['nsnManagerAccountName'][0]
        filter = '(uid=%s)'%lineManagerAccountId
        attrs = ['sn', 'mail', 'cn', 'displayName', 'nsnManagerAccountName']
        base_dn = 'o=NSN'
        lineResult = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)
        # lineManagerDisplayName = lineResult[0][1]['displayName'][0]
        # lineManagerEmail = lineResult[0][1]['mail'][0]
        try:
            lineManagerEmail = lineResult[0][1]['mail'][0]
        except:
            lineManagerEmail = ''
        return lineManagerEmail
    else:
        return ''


class SquadGroupAssessor(db.Model):
    __tablename__ = 'squadGroupAssessorTable'
    assessorId = db.Column('assessorId', db.String(64), primary_key=True)
    squadGroupRcaEdaAssessor = db.Column(db.String(64))
    tribeRcaEdaLeadAssessor = db.Column(db.String(64))
    assessorSquadGroupName = db.Column(db.String(64))
    assessorSquadGroupLead = db.Column(db.String(64))
    assessorTribe = db.Column(db.String(64))
    assessorTribeLead = db.Column(db.String(64))
    squadGroupEmailGroup = db.Column(db.String(64))
    registeredBy = db.Column(db.String(64))

    def __init__(self, assessorId,squadGroupRcaEdaAssessor,tribeRcaEdaLeadAssessor,assessorSquadGroupName,assessorSquadGroupLead,\
                 assessorTribe,assessorTribeLead,squadGroupEmailGroup,registeredBy):

        self.assessorId = assessorId
        self.squadGroupRcaEdaAssessor = squadGroupRcaEdaAssessor
        self.tribeRcaEdaLeadAssessor = tribeRcaEdaLeadAssessor
        self.assessorSquadGroupName = assessorSquadGroupName
        self.assessorSquadGroupLead = assessorSquadGroupLead
        self.assessorTribe = assessorTribe
        self.assessorTribeLead = assessorTribeLead
        self.squadGroupEmailGroup = squadGroupEmailGroup
        self.registeredBy = registeredBy

def getAccountIdByEmailName(JiraIssueAssignee):
    #AssignTo = JiraIssueAssignee
    # user = JiraUser.query.filter_by(email=JiraIssueAssignee).first()
    # if user:
    #     AssignTo = user.username
    # else:
    if JiraIssueAssignee == '':
        return JiraIssueAssignee
    flg=True
    try:
        conn = get_ldap_connection()
    except:
        # flg=False
        return redirect(url_for('login'))
    # if flg:
    #     return ''
    filter = '(mail=%s)' % JiraIssueAssignee
    attrs = ['sn', 'mail', 'cn', 'displayName', 'uid']
    base_dn = 'o=NSN'
    flg=True
    try:
        result = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)
    except:
        flg=False
        print 'No such account!!!'
        AssignTo =''
        # return AssignTo
        # pass
    AssignTo = ''
    if flg and result:
        AssignTo = result[0][1]['uid'][0]
    return AssignTo


def getAccountIdByEmailName(JiraIssueAssignee):
    #AssignTo = JiraIssueAssignee
    # user = JiraUser.query.filter_by(email=JiraIssueAssignee).first()
    # if user:
    #     AssignTo = user.username
    # else:
    if JiraIssueAssignee == '':
        return JiraIssueAssignee
    flg=True
    try:
        conn = get_ldap_connection()
    except:
        # flg=False
        return redirect(url_for('login'))
    # if flg:
    #     return ''
    filter = '(mail=%s)' % JiraIssueAssignee
    attrs = ['sn', 'mail', 'cn', 'displayName', 'uid']
    base_dn = 'o=NSN'
    flg=True
    try:
        result = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)
    except:
        flg=False
        print 'No such account!!!'
        AssignTo =''
        # return AssignTo
        # pass
    AssignTo = ''
    if flg and result:
        AssignTo = result[0][1]['uid'][0]
    return AssignTo


def getGroupInChargeInfo(PRID,PRGroupInCharge):
    groupInChargeInfo = tryGetGroupInChargeInfo(PRID, PRGroupInCharge)
    return groupInChargeInfo

class InChargeGroup(db.Model):
    __tablename__ = "inchargegroups"
    # id = db.Column('index',db.Integer)
    id = db.Column(db.Integer,primary_key=True)
    InChargeGroupName = db.Column(db.String(128))
    AssessorEmail = db.Column(db.String(64),index=True)
    Labels = db.Column(db.String(128))
    BusinessUnit = db.Column(db.String(128))
    BusinessLine = db.Column(db.String(128))
    ProductLine = db.Column(db.String(128),default='All')
    JIRAProject = db.Column(db.String(128))
    AddedBy = db.Column(db.String(64))
    registered_on = db.Column('registered_on', db.DateTime)
    BG = db.Column(db.String(64))
    DU = db.Column(db.String(64))
    Tribe = db.Column(db.String(64))
    RCAFilter = db.Column(db.String(128))
    EDA_AssessorEmail = db.Column(db.String(128))
    EDACreatingTime = db.Column(db.String(128))
    EdaCaseType = db.Column(db.String(128))
    RCAEDACategory = db.Column(db.String(128))

    # user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))

    def __init__(self , InChargeGroupName ,AssessorEmail,Labels,BusinessUnit,BusinessLine,ProductLine,JIRAProject,AddedBy, \
                 BG, DU, Tribe,RCAFilter,EDA_AssessorEmail,EDACreatingTime,EdaCaseType,RCAEDACategory):
        self.InChargeGroupName = InChargeGroupName
        self.AssessorEmail = AssessorEmail
        self.Labels = Labels
        self.BusinessUnit = BusinessUnit
        self.BusinessLine = BusinessLine
        self.ProductLine = ProductLine
        self.JIRAProject = JIRAProject
        self.AddedBy = AddedBy
        self.registered_on = datetime.datetime.now()
        self.BG = BG
        self.DU = DU
        self.Tribe = Tribe
        self.RCAFilter = RCAFilter
        self.EDA_AssessorEmail = EDA_AssessorEmail
        self.EDACreatingTime = EDACreatingTime
        self.EdaCaseType = EdaCaseType
        self.RCAEDACategory = RCAEDACategory

def tryGetGroupInChargeInfo(PRID,PRGroupInCharge):
    groupInChargeInfo = ''
    BusinessLine,ProductLine = getBusinessLineAndProductLine(PRID)
    groupInChargeInfo = InChargeGroup.query.get(1)
    groupInChargeInfo = InChargeGroup.query.filter_by(InChargeGroupName=PRGroupInCharge, \
                                                     BusinessLine=BusinessLine,
                                                     ProductLine='All').first()
    # print 'get All'
    if not groupInChargeInfo:
        groupInChargeInfo = InChargeGroup.query.filter_by(InChargeGroupName=PRGroupInCharge, \
                                                         BusinessLine=BusinessLine,
                                                         ProductLine=ProductLine).first()
    # print 'get Productline first'
    if not groupInChargeInfo:
        groupInChargeInfo = InChargeGroup.query.filter_by(InChargeGroupName=PRGroupInCharge, \
                                                         AddedBy='sufang.huang@nokia-sbell.com').first()
    # print 'get AddedBy'
    if not groupInChargeInfo:
        num = InChargeGroup.query.filter_by(InChargeGroupName=PRGroupInCharge).count()
        if num == 1:
            groupInChargeInfo = InChargeGroup.query.filter_by(InChargeGroupName=PRGroupInCharge).first()
        # elif num == 0:
        #     print 'No registerred yet'
        # else:
        #     print 'There are shared GIC....'
    # print 'get by GIC only'
    return groupInChargeInfo


def getFaRcaEdaStatus(PRID):
    url1 = "https://pronto.inside.nsn.com/prontoapi/rest/api/latest/problemReport/%s" % PRID
    r = requests.get(url1, verify=False, auth=('krma', 'Nokia123'))
    r_status = r.status_code
    if r_status != 200:
        return True
    a = json.loads(r.text)
    faultAnalysisId = a['faultAnalysisId']
    urlfa = 'https://pronto.int.net.nokia.com/prontoapi/rest/api/1/faultAnalysis/%s' % faultAnalysisId
    # urlfa = 'https://pronto.int.net.nokia.com/prontoapi/rest/api/1/faultAnalysis/FA715953'
    r = requests.get(urlfa, verify=False, auth=('krma', 'Nokia123'))
    r_status = r.status_code
    if r_status != 200:
        return True
    b = json.loads(r.text)
    if 'rcaEdaDecision' in b.keys():
        rcaEdaDecision = b['rcaEdaDecision']
    else:
        print "No rcaEdaDecision for PRID = %s faultAnalysisId = %s" %(PRID,faultAnalysisId)
        rcaEdaDecision = ''
    # rcaEdaDecision = b['rcaEdaDecision']
    # FaRcaEdaStatus = b['rcaEda']['status']
    if 'rcaEda' in b.keys():
        FaRcaEdaStatus = b['rcaEda']['status']
    else:
        print "No rcaEda for PRID = %s faultAnalysisId = %s" %(PRID,faultAnalysisId)
        FaRcaEdaStatus = ''
    if rcaEdaDecision == 'Yes' and FaRcaEdaStatus == None:
        return False
    else:
        return True


def FaCreateAndAssign(jira,PRID,PRAttached):
    FaRcaEdaStatus = getFaRcaEdaStatus(PRID)
    if FaRcaEdaStatus:
        return False
    todo_item = MnTodo.query.get(PRID)
    exceptionFlag, existingFlag = checkJiraExistingDiff(jira, PRID, PRAttached)
    if exceptionFlag:
        return False
    if exceptionFlag == False and existingFlag:
    # if checkJiraExisting(jira, PRID, PRAttached):
        todo_item.JiraTaskIsCreated = 'Yes'
        db.session.commit()
        return False
    # todo_item = MnTodo.query.get(PRID)
    # AddedBy = inchargegroupinfo.AddedBy
    # watcher = getAccountIdByEmailName(AddedBy)
    # todo_item = MnTodo.query.get(PRID)
    InChargeGroupName = todo_item.PRGroupInCharge
    # BusinessLine = todo_item.BusinessLine
    # ProductLine =  todo_item.ProductLine
    # inchargegroupinfo = InChargeGroup.query.get(InChargeGroupName)
    # inchargegroupinfo = InChargeGroup.query.filter_by(InChargeGroupName=InChargeGroupName, \
    #                                                   BusinessLine=BusinessLine,
    #                                                   ProductLine='All').first()
    # if not inchargegroupinfo:
    #     inchargegroupinfo = InChargeGroup.query.filter_by(InChargeGroupName=InChargeGroupName, \
    #                                                       BusinessLine=BusinessLine,
    #                                                       ProductLine=ProductLine).first()
    # if not inchargegroupinfo:
    #     inchargegroupinfo = InChargeGroup.query.filter_by(InChargeGroupName=InChargeGroupName,\
    #                                                      AddedBy='sufang.huang@nokia-sbell.com').first()
    inchargegroupinfo = getGroupInChargeInfo(PRID, InChargeGroupName)
    # if inchargegroupinfo:
    #     AddedBy = inchargegroupinfo.AddedBy
    if inchargegroupinfo:
        # CaseType = inchargegroupinfo.ProductLine.strip()
        CaseType = inchargegroupinfo.RCAEDACategory.strip()
        JiraIssueAssignee = inchargegroupinfo.AssessorEmail.strip()
        EdaCaseType = inchargegroupinfo.EdaCaseType
        if len (JiraIssueAssignee.split('.com')) > 2:
            try:
                a = JiraIssueAssignee.split(';')
            except:
                pass
            JiraIssueAssignee = a[0]
    else:
        return False
    AddedBy = inchargegroupinfo.AddedBy
    watcher = getAccountIdByEmailName(AddedBy)
    # print 'JiraIssueAssignee=%s!!!!!!!!!!!!!!!!!!!!!!!!%s' % (JiraIssueAssignee,PRID)
    AssigneeEmail = JiraIssueAssignee
    JiraIssueAssignee = getAccountIdByEmailName(JiraIssueAssignee)
    operation_status,issue = createParent5WhyRcaTaskFirst(jira, PRID)
    # issue = jira.issue('MNRCA-23091')
    # PRID='PR436520'
    if operation_status == False:
        return False
    RcaAnalysisSubtaskKey = issue.key
    ProntoInfo = issue.fields.summary
    # # Jira RCA Analysis Subtask
    # CaseType = 'RCA'
    # JiraIssueAssignee = ''
    # todo_item = MnTodo.query.get(PRID)
    # InChargeGroupName = todo_item.PRGroupInCharge
    # inchargegroupinfo = InChargeGroup.query.get(InChargeGroupName)
    # if inchargegroupinfo:
    #     CaseType = inchargegroupinfo.ProductLine.strip()
    #     JiraIssueAssignee = inchargegroupinfo.AssessorEmail.strip()
    #     EdaCaseType = inchargegroupinfo.EdaCaseType
    #     if len (JiraIssueAssignee.split('.com')) > 2:
    #         try:
    #             a = JiraIssueAssignee.split(';')
    #         except:
    #             pass
    #         JiraIssueAssignee = a[0]
    # else:
    #     return False
    # print 'JiraIssueAssignee=%s!!!!!!!!!!!!!!!!!!!!!!!!%s' % (JiraIssueAssignee,PRID)
    # JiraIssueAssignee = getAccountIdByEmailName(JiraIssueAssignee)
    summaryinfo = '%s for ' % CaseType + PRID
    # CaseType = AnalysisIssueCaseType[CaseType]
    # dueDate = (datetime.datetime.now() + datetime.timedelta(days=20)).strftime("%Y-%m-%d")
    rcaDueDate = (datetime.datetime.now() + datetime.timedelta(days=15)).strftime("%Y-%m-%d")
    dueDate = (datetime.datetime.now() + datetime.timedelta(days=15)).strftime(
        "%Y-%m-%dT%H:%M:00.00+0200")
    # todo_item = MnTodo.query.get(PRID)
    # AddedBy = inchargegroupinfo.AddedBy
    # watcher = getAccountIdByEmailName(AddedBy)
    JiraIssueProductLine = todo_item.ProductLine
    reporter = watcher
    if JiraIssueProductLine == 'TD LTE':
        reporter = 'bqgk83'
    if JiraIssueProductLine == 'FDD LTE':
        reporter = 'vdh483'
    if AddedBy == 'vladimir.nazarkin@nokia.com' and \
            todo_item.PRProduct.strip() == 'Flexi Multiradio BTS SingleRAN':
        # reporter = 'wro02917'
        reporter = 'vdh483'
    if todo_item.PRRcaEdaAssessor =='piotr.laskowski@nokia.com' or \
            AddedBy == 'piotr.laskowski@nokia.com':
        if todo_item.PRProduct.strip() != 'Flexi Multiradio BTS SingleRAN':
            reporter = 'pilaskow'
        else:
            # reporter = 'wro02917'
            reporter = 'vdh483'
    if CaseType == 'RCA' or CaseType == 'RCA and EDA':
        CaseType = AnalysisIssueCaseType[CaseType]
        issueaddforRCAsubtask = {
            'project': {'id': u'41675'},
            'parent': {"key": RcaAnalysisSubtaskKey},
            'issuetype': {'id': u'19800'},  # Analysis subtask
            'summary': summaryinfo,
            'customfield_10464': {'id': CaseType},  # Case Type
            'customfield_27792': dueDate,
            'assignee': {'name': JiraIssueAssignee},
            'reporter': {'name': reporter},
            # 'watcher': {'name': watcher},
        }
        newissue = jira.create_issue(issueaddforRCAsubtask)
        jira.remove_watcher(newissue, 'qmxh38')
        jira.add_watcher(newissue, watcher)
        url = "https://pronto.inside.nsn.com/prontoapi/rest/api/latest/problemReport/%s" % PRID
        r = requests.get(url, verify=False, auth=('krma', 'Nokia123'))
        # addTodo(PRID, newissue.key, AssigneeEmail, r, rcaDueDate)
        # addToJiraTodo(newissue, PRID)
        # MnRcaMetricsUpdateNew(newissue,jira)
        MnRcaMetricsUpdateWithAssignee(AssigneeEmail,newissue,jira)
        return True
    if EdaCaseType == 'EDA':
        EDA_AssessorEmail = inchargegroupinfo.EDA_AssessorEmail.strip()
        EDACreatingTime = inchargegroupinfo.EDACreatingTime.strip()
        CaseType = AnalysisIssueCaseType[EdaCaseType]
        summaryinfo = '%s for ' % EdaCaseType + PRID
        edaDueDate = (datetime.datetime.now() + datetime.timedelta(days=45)).strftime("%Y-%m-%d")
        dueDate = (datetime.datetime.now() + datetime.timedelta(days=45)).strftime(
            "%Y-%m-%dT%H:%M:00.00+0200")
        if EDACreatingTime == 'Together With RCA':
            JiraIssueAssignee = getAccountIdByEmailName(EDA_AssessorEmail)
            issueaddforRCAsubtask = {
                'project': {'id': u'41675'},
                'parent': {"key": RcaAnalysisSubtaskKey},
                'issuetype': {'id': u'19800'},  # Analysis subtask
                'summary': summaryinfo,
                'customfield_10464': {'id': CaseType},  # Case Type
                'customfield_27792': dueDate,
                'assignee': {'name': JiraIssueAssignee},
                'reporter': {'name': reporter},
                # 'watcher': {'name': watcher},
            }
            newissue = jira.create_issue(issueaddforRCAsubtask)
            jira.remove_watcher(newissue, 'qmxh38')
            jira.add_watcher(newissue, watcher)
            db.session.commit() # flush the buffer to DB
            # updateEdaInfo(PRID,newissue,EDA_AssessorEmail,edaDueDate)
            # addToJiraTodo(newissue, PRID)
            # MnRcaMetricsUpdateNew(newissue,jira)
            MnRcaMetricsUpdateWithAssignee(EDA_AssessorEmail, newissue, jira)
            return True
    if CaseType == 'RCA Subtask':
        summaryinfo = "RCA for %s" % ProntoInfo
        if len(summaryinfo) > 255:
            summaryinfo = summaryinfo[0:255]
        issueaddforRCAsubtask = {
            'project': {'id': u'41675'},
            'parent': {"key": RcaAnalysisSubtaskKey},
            'issuetype': {'id': u'278'},  # RCA subtask
            'summary': summaryinfo,
            # 'customfield_10464': {'id': CaseType},  # Case Type
            # 'customfield_27792': dueDate,
            'assignee': {'name': JiraIssueAssignee},
            'reporter': {'name': reporter},
            # 'watcher': {'name': watcher},
        }
        newissue = jira.create_issue(issueaddforRCAsubtask)
        jira.remove_watcher(newissue, 'qmxh38')
        jira.add_watcher(newissue, watcher)

        url = "https://pronto.inside.nsn.com/prontoapi/rest/api/latest/problemReport/%s" % PRID
        r = requests.get(url, verify=False, auth=('krma', 'Nokia123'))
        try:
            addTodo(PRID, newissue.key, AssigneeEmail, r, rcaDueDate)
        except:
            pass
        # addToJiraTodo(newissue, PRID)
    if EdaCaseType == 'EDA subtask':
        EDA_AssessorEmail = inchargegroupinfo.EDA_AssessorEmail.strip()
        EDACreatingTime = inchargegroupinfo.EDACreatingTime.strip()
        if EDACreatingTime == 'Together With RCA':
            JiraIssueAssignee = getAccountIdByEmailName(EDA_AssessorEmail)
            summaryinfo = "EDA for %s" % ProntoInfo
            if len(summaryinfo) > 255:
                summaryinfo = summaryinfo[0:255]
            issueaddforRCAsubtask = {
                'project': {'id': u'41675'},
                'parent': {"key": RcaAnalysisSubtaskKey},
                'issuetype': {'id': u'17768'},  # RCA subtask = 278, EDA subtask=17768
                'summary': summaryinfo,
                # 'customfield_10464': {'id': CaseType},  # Case Type
                # 'customfield_27792': dueDate,
                'assignee': {'name': JiraIssueAssignee},
                # 'reporter': {'name': reporter},
                # 'watcher': {'name': watcher},
            }
            newissue = jira.create_issue(issueaddforRCAsubtask)
            jira.remove_watcher(newissue, 'qmxh38')
            jira.add_watcher(newissue, watcher)
            edaDueDate = (datetime.datetime.now() + datetime.timedelta(days=45)).strftime("%Y-%m-%d")
            db.session.commit()
            updateEdaInfo(PRID, newissue, EDA_AssessorEmail, edaDueDate)
            # addToJiraTodo(newissue, PRID)


def checkLocalExisting(PRID,PRAttached):
    existingFlag = False
    todo_item = Todo.query.filter_by(PRID=PRID).all()
    if len(todo_item):
        existingFlag = True
        return existingFlag
    if PRAttached:
        attachedList = PRAttached.split(',')
        for PRID in attachedList:
            todo_item = Todo.query.filter_by(PRID=PRID).all()
            if len(todo_item):
                existingFlag = True
                return existingFlag
    return existingFlag


class MnTodo(db.Model):
    __tablename__ = 'mnrcatable'
    # JiraIssueId = db.Column('JiraIssueId', db.String(64), primary_key=True)
    PRID = db.Column('PRID', db.String(64),primary_key=True)
    PRTitle = db.Column(db.String(1024))
    PRReportedDate = db.Column(db.String(64))
    PRClosedDate=db.Column(db.String(64))
    PRRelease = db.Column(db.String(128))
    PRAttached = db.Column(db.String(512))
    PRSeverity = db.Column(db.String(32))
    PRGroupInCharge = db.Column(db.String(64))
    PRRcaEdaAssessor = db.Column(db.String(128))
    PRProduct = db.Column(db.String(64))
    ReportedBy = db.Column(db.String(64))
    FaultCoordinator = db.Column(db.String(64))
    CustomerName = db.Column(db.String(128))
    BusinessUnit = db.Column(db.String(128))  # Parent task has, Child task does not have
    BusinessLine = db.Column(db.String(128)) # Parent task has, Child task does not have
    ProductLine = db.Column(db.String(128))  # Parent task has, Child task does not have
    Feature = db.Column(db.String(128))
    RCAEDACategory = db.Column(db.String(128))
    JiraCustomerName= db.Column(db.String(128))
    JIRAProject= db.Column(db.String(128))
    FaRcaEdaDecisionFlag= db.Column(db.String(32))
    EDA_AssessorEmail = db.Column(db.String(128))
    EDACreatingTime = db.Column(db.String(128))
    EdaCaseType = db.Column(db.String(128))
    JiraTaskIsCreated = db.Column(db.String(32))

    user_id = db.Column(db.Integer, db.ForeignKey('jirausers.user_id'))

    def __init__(self, PRID,PRTitle,PRReportedDate,PRClosedDate,PRRelease,PRSeverity,PRGroupInCharge,PRAttached,PRRcaEdaAssessor,\
                 PRProduct,ReportedBy,FaultCoordinator,CustomerName,BusinessUnit,BusinessLine,ProductLine,Feature,RCAEDACategory, \
                 JiraCustomerName,JIRAProject,FaRcaEdaDecisionFlag,EDA_AssessorEmail,EDACreatingTime,EdaCaseType,JiraTaskIsCreated):
        self.PRID = PRID
        self.PRTitle = PRTitle
        self.PRReportedDate = PRReportedDate
        self.PRClosedDate = PRClosedDate
        self.PRRcaEdaAssessor = PRRcaEdaAssessor
        self.PRRelease = PRRelease
        self.PRAttached = PRAttached
        self.PRSeverity = PRSeverity
        self.PRGroupInCharge = PRGroupInCharge
        self.PRProduct = PRProduct
        self.ReportedBy = ReportedBy
        self.FaultCoordinator = FaultCoordinator
        self.CustomerName = CustomerName
        self.BusinessUnit = BusinessUnit
        self.BusinessLine = BusinessLine
        self.ProductLine = ProductLine
        self.Feature = Feature
        self.RCAEDACategory = RCAEDACategory
        self.JiraCustomerName = JiraCustomerName
        self.JIRAProject = JIRAProject
        self.FaRcaEdaDecisionFlag = FaRcaEdaDecisionFlag
        self.EDA_AssessorEmail = EDA_AssessorEmail
        self.EDACreatingTime = EDACreatingTime
        self.EdaCaseType = EdaCaseType
        self.JiraTaskIsCreated = JiraTaskIsCreated

def daysBetweenDate(start,end):
    year1=int(start.split('-',2)[0])
    month1=int(start.split('-',2)[1])
    day1=int(start.split('-',2)[2])

    year2=int(end.split('-',2)[0])
    month2=int(end.split('-',2)[1])
    day2=int(end.split('-',2)[2])
    # print ("daysBetweenDates(year1, month1, day1, year2, month2, day2)=%d"%daysBetweenDates(year1, month1, day1, year2, month2, day2))
    return daysBetweenDates(year1, month1, day1, year2, month2, day2)


def comparetime(start_t, end_t):
    s_time = time.mktime(time.strptime(start_t, '%Y-%m-%d'))
    # get the seconds for specify date
    e_time = time.mktime(time.strptime(end_t, '%Y-%m-%d'))
    if (float(e_time) - float(s_time)) > float(86400):
        print ("@@@float(e_time)- float(s_time))=%f" % (float(e_time) - float(s_time)))
        return True
    return False


def leap_year(y):
    if (y % 4 == 0 and y % 100 != 0) or y % 400 == 0:
        return True
    else:
        return False


def days_in_month(y, m):
    if m in [1, 3, 5, 7, 8, 10, 12]:
        return 31
    elif m in [4, 6, 9, 11]:
        return 30
    else:
        if leap_year(y):
            return 29
        else:
            return 28


def days_this_year(year):
    if leap_year(year):
        return 366
    else:
        return 365


def days_passed(year, month, day):
    m = 1
    days = 0
    while m < month:
        days += days_in_month(year, m)
        m += 1
    return days + day


def dateIsBefore(year1, month1, day1, year2, month2, day2):
    """Returns True if year1-month1-day1 is before year2-month2-day2. Otherwise, returns False."""
    if year1 < year2:
        return True
    if year1 == year2:
        if month1 < month2:
            return True
        if month1 == month2:
            return day1 < day2
    return False

def daysBetweenDates(year1, month1, day1, year2, month2, day2):
    if year1 == year2:
        return days_passed(year2, month2, day2) - days_passed(year1, month1, day1)
    if year1 < year2:
        sum1 = 0
        y1 = year1
        while y1 < year2:
            sum1 += days_this_year(y1)
            y1 += 1
        daysYear1 = days_passed(year1,month1,day1)
        daysYear2 = days_passed(year2,month2,day2)
        daysPassed = sum1 - daysYear1 + daysYear2
        return daysPassed
    if year1 > year2:
        sum1 = 0
        y1 = year1
        while y1 > year2:
            sum1 -= days_this_year(y1)
            y1 -= 1
        daysYear1 = days_passed(year1,month1,day1)
        daysYear2 = days_passed(year2,month2,day2)
        daysPassed = sum1 - daysYear1 + daysYear2
        # return sum1-days_passed(year1,month1,day1)+days_passed(year2,month2,day2)
        return daysPassed

def MnRcaMetricsUpdateWithAssignee(JiraIssueAssigneeEmail,issue,jira):
    # print 'JiraIssueId = %s' %JiraIssueId
    # issue = jira.issue(JiraIssueId)
    JiraIssueId = issue.key
    # project = issue.fields.project.key
    Rca5WhyParentIssue = issue.fields.parent
    JiraIssueParentTaskId = str(Rca5WhyParentIssue.key)
    Rca5WhyParentIssue = jira.issue(JiraIssueParentTaskId)
    summary = strip_non_ascii(Rca5WhyParentIssue.fields.summary)
    JiraIssueSummary = strip_non_ascii(Rca5WhyParentIssue.fields.summary)
    # print('MnRcaMetricsUpdateWithAssignee  JiraIssueId =' + str(JiraIssueId))
    #Rca5WhyParentIssue = jira.issue(JiraIssueParentTaskId)
    JiraIssueType = issue.fields.issuetype.name

    try:
        PRID = summary
        PRID = PRID.split(':')
        PRID = PRID[0].strip()
        PRID = PRID.split(' ')
        PRID = PRID[0]
    except:
        print "Bad@@@@@@@@@@@@@@@@" + summary
        return False, ''
    PRID = PRID
    if len(PRID) > 64:
        PRID = PRID[:64]

    url = "https://pronto.inside.nsn.com/prontoapi/rest/api/latest/problemReport/%s" % PRID
    r = requests.get(url, verify=False, auth=(gAdmin, gAuth))
    a = r.json()

    PRGroupInCharge = a['groupIncharge']
    PRSeverity = a['severity']
    author = a['author']
    PRAttached = a['problemReportIds']
    # attachedlist = PRAttached
    if not PRAttached:
        PRAttached = ''
    else:
        LabelItems = PRAttached
        b = ''
        for s in LabelItems:
            b = b + s + ','
            PRAttached = b.strip(',')
    PRTitle = a['title']
    FAID = a['faultAnalysisId']
    # ReportedBy = a['reportedBy']
    if author == 'Electra':
        ReportedBy = 'Customer'
    else:
        ReportedBy = 'Nokia'

    JiraIssueCaseType = ''
    if JiraIssueType in ('Analysis subtask',):
        JiraIssueCaseType = str(issue.fields.customfield_10464)
    JiraIssueStatus = issue.fields.status.name
    JiraIssueParentStatus = Rca5WhyParentIssue.fields.status.name
    JiraIssueAssignee = issue.fields.assignee
    if not JiraIssueAssignee:
    #     print "JiraIssueAssignee = str(issue.fields.assignee) JiraIssueAssignee = %s" % JiraIssueAssignee
    # else:
        print "JiraIssueAssignee = str(issue.fields.assignee) is empty JiraIssueId = %s !!!!!!!!!!!!!!!!!!!!!!!" %JiraIssueId
    JiraIssueReporter = issue.fields.reporter.displayName

    createDate = issue.fields.created
    JiraIssueCreatedDate = createDate.split('T')[0]
    createdFlg = False
    try:
        createDate = Rca5WhyParentIssue.fields.created
    except:
        createdFlg = True
        pass
    if createdFlg:
        print 'createDate = Rca5WhyParentIssue.fields.created'

    JiraIssueParentCreatedDate = createDate.split('T')[0]

    # print "Before MnRcaMetricsUpdateWithAssignee JiraIssueAssigneeEmail =%s" % JiraIssueAssigneeEmail
    # JiraIssueAssigneeEmail = ''
    # if issue.fields.assignee:
    #     JiraIssueAssigneeEmail = issue.fields.assignee.emailAddress
    conn = get_ldap_connection()
    JiraIssueAssignee,LineManagerEmail,squadGroup,lineDisplayName,tribeLeadDisplayName,tribeName = \
        getDisplayNameSquadTribeInfoWithConn(JiraIssueAssigneeEmail,conn)
    # print "MnRcaMetricsUpdateWithAssignee JiraIssueAssigneeEmail =%s,tribeName=%s" %(JiraIssueAssigneeEmail,tribeName)
    # JiraIssueAssignee = getDisplayNameByEmailName(JiraIssueAssigneeEmail)
    PRRcaEdaAssessor = lineDisplayName
    JiraIssueAssigneeSquadGroupLead = lineDisplayName
    JiraIssueAssigneeTribeLead = tribeLeadDisplayName #"zhuofei.chen@nokia-sbell.com"
    JiraIssueAssigneeTribe =tribeName
    JiraIssueAssigneeSquadGroup =squadGroup
    JiraIssueDueDate =''
    if JiraIssueType == 'Analysis subtask':
        dueDate = issue.fields.customfield_27792
        if dueDate:
            JiraIssueDueDate = dueDate.split('T')[0]
    current_date = datetime.datetime.now()  # + datetime.timedelta(days=days)
    current_date = current_date.strftime('%Y-%m-%d')
    JiraIssueResolutionDate = current_date
    JiraIssueParentResolutionDate = current_date
    if JiraIssueStatus in ['Resolved', 'Closed', 'RCA Done', 'EDA Done', 'RCA Action Done']:
        resolutiondate = str(issue.fields.resolutiondate)
        JiraIssueResolutionDate = resolutiondate.split('T')[0]
    if JiraIssueParentStatus in ['Resolved', 'Closed']:
        resolutiondate = str(Rca5WhyParentIssue.fields.resolutiondate)
        JiraIssueParentResolutionDate = resolutiondate.split('T')[0]

    JiraIssueOpenDays = daysBetweenDate(JiraIssueCreatedDate, JiraIssueResolutionDate)
    JiraIssueOverDue = 'No'
    JiraIssueParentOpenDays = daysBetweenDate(JiraIssueParentCreatedDate, JiraIssueParentResolutionDate)
    JiraIssueParentOverDue = 'No'
    if JiraIssueParentOpenDays > 30:
        JiraIssueParentOverDue = 'Yes'

    PRRcaEdaAssessor = PRRcaEdaAssessor
    PRTitle = strip_non_ascii(PRTitle)
    todo_item = MnRcaMetrics.query.get(JiraIssueId)
    if todo_item:
        print "MnRcaMetricsUpdateWithAssignee return"
        return
    else:
        JiraIssueOverDueReason = ''
        JiraIssueParentOverDueReason = ''
        # print "MnRcaMetricsUpdateWithAssignee JiraIssueAssignee = %s" % JiraIssueAssignee
        todo = MnRcaMetrics(JiraIssueId,JiraIssueParentTaskId,JiraIssueSummary,JiraIssueType,JiraIssueCaseType,\
             JiraIssueStatus,JiraIssueParentStatus,JiraIssueAssignee,JiraIssueReporter,PRID,FAID,PRTitle,\
             PRRcaEdaAssessor,PRAttached,PRSeverity,PRGroupInCharge,JiraIssueCreatedDate,JiraIssueParentCreatedDate,\
             JiraIssueResolutionDate,JiraIssueParentResolutionDate,JiraIssueDueDate,JiraIssueOpenDays,\
             JiraIssueParentOpenDays,JiraIssueAssigneeSquadGroup,JiraIssueAssigneeSquadGroupLead,\
             JiraIssueAssigneeTribe,JiraIssueAssigneeTribeLead,JiraIssueOverDue,JiraIssueParentOverDue,\
             JiraIssueOverDueReason,JiraIssueParentOverDueReason,ReportedBy)
        db.session.add(todo)
        db.session.commit()


def getDisplayNameSquadTribeInfoWithConn(JiraIssueAssignee, conn):
    AssignTo = JiraIssueAssignee.strip()
    if JiraIssueAssignee == '':
        return '', '', '', '', ''
    # conn = get_ldap_connection()
    filter = '(mail=%s)' % AssignTo
    # Title:'Squad Group Lead', 'Tribe Leader', 'NSB MN SRAN RD L2 HZH'
    # nsnTeamName:'NSB MN SRAN RD L2 HZH Arch Ops',
    # conn = app.config['ldap']
    attrs = ['mail', 'displayName', 'nsnManagerAccountName', 'nsnTeamName', 'title']
    base_dn = 'o=NSN'
    # conn = app.config['ldap']
    result = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)
    if not result:
        return '', '', '', '', ''
    if 'title' in result[0][1].keys():
        title = result[0][1]['title'][0]
        title = title.split(',')[0]
    else:
        title = ''
    if 'displayName' in result[0][1].keys():
        displayName = result[0][1]['displayName'][0]
    else:
        displayName = ''
    if 'nsnTeamName' in result[0][1].keys():
        squadGroupName = result[0][1]['nsnTeamName'][0]
        # nsnTeamName=result[0][1]['nsnOperativeOrgName'][0]
    else:
        squadGroupName = 'External People'
    if 'nsnManagerAccountName' in result[0][1].keys():
        lineManagerAccountId = result[0][1]['nsnManagerAccountName'][0]
    else:
        print 'JiraAssigneeEmail=%s' % JiraIssueAssignee
        return displayName,'', squadGroupName, '', '', ''
    if len(title.split('Tribe Lead')) > 1 or len(title.split('Head of')) > 1:
    # if title in ['Tribe Leader', 'R&D Tribe Leader']:
        # lineDisplayName = lineDisplayName1
        # tribeLeadDisplayName = displayName
        tribeName = squadGroupName
        # lineManagerEmail = lineManagerEmail1
        return displayName,'', squadGroupName, '', '', tribeName

    filter = '(uid=%s)' % lineManagerAccountId
    attrs = ['mail', 'displayName', 'nsnManagerAccountName', 'nsnTeamName', 'title']
    # 'nsnTeamName','title'
    base_dn = 'o=NSN'
    lineResult = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)
    if 'title' in lineResult[0][1].keys():
        title1 = lineResult[0][1]['title'][0]
        title1 = title1.split(',')[0]
    else:
        title1 = ''
    if 'nsnTeamName' in lineResult[0][1].keys():
        squadGroupName1 = lineResult[0][1]['nsnTeamName'][0]
    else:
        squadGroupName1 = 'External Squad'
    if 'displayName' in lineResult[0][1].keys():
        lineDisplayName1 = lineResult[0][1]['displayName'][0]
    else:
        lineDisplayName1 = ''
    if 'mail' in lineResult[0][1].keys():
        lineManagerEmail1 = lineResult[0][1]['mail'][0]
    else:
        lineManagerEmail1 = ''
    if 'nsnManagerAccountName' in lineResult[0][1].keys():
        lineManagerAccountId1 = lineResult[0][1]['nsnManagerAccountName'][0]
    else:
        squadGroupName = squadGroupName1
        return displayName,lineManagerEmail1, squadGroupName, lineDisplayName1, '', ''

    # if title1 in ['Tribe Leader', 'R&D Tribe Leader','Head of NM RD UTF']:
    if len(title1.split('Tribe Lead')) > 1 or len(title1.split('Head of')) > 1:
        # lineDisplayName = lineDisplayName1
        # tribeLeadDisplayName = displayName
        tribeName = squadGroupName1
        # lineManagerEmail = lineManagerEmail1
        return displayName,lineManagerEmail1, squadGroupName, lineDisplayName1, lineDisplayName1, tribeName
    # if title == 'Squad Group Lead':
    if len(title.split('Squad Group Lead')) > 1:
        tribeName = squadGroupName1
        tribeLeadDisplayName = lineDisplayName1
        lineManagerEmail = lineManagerEmail1
        lineDisplayName = lineDisplayName1
        return displayName,lineManagerEmail, squadGroupName, lineDisplayName, tribeLeadDisplayName, tribeName
    if len(title.split('Tribe Lead')) > 1 or len(title.split('Head of')) > 1:
    # if title in ['Tribe Leader', 'R&D Tribe Leader']:
        lineDisplayName = lineDisplayName1
        tribeLeadDisplayName = displayName
        tribeName = squadGroupName
        lineManagerEmail = lineManagerEmail1
        return displayName,lineManagerEmail, squadGroupName, lineDisplayName, tribeLeadDisplayName, tribeName
    if len(title.split('Tribe Lead')) == 1 and len(title.split('Head of')) == 1 and \
        len(title.split('Squad Group Lead')) == 1:
    # if title not in ['Squad Group Lead', 'Tribe Leader', 'R&D Tribe Leader']:
        # Next Level Org:
        squadGroupName = squadGroupName1
        TribeLeadAccountId = lineManagerAccountId1
        filter = '(uid=%s)' % TribeLeadAccountId
        attrs = ['mail', 'displayName', 'nsnManagerAccountName', 'nsnTeamName', 'title']
        base_dn = 'o=NSN'
        TribeLeadResult = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)
        tribeLeadDisplayName = TribeLeadResult[0][1]['displayName'][0]
        tribeName = TribeLeadResult[0][1]['nsnTeamName'][0]
        lineManagerEmail = lineManagerEmail1
        lineDisplayName = lineDisplayName1
        return displayName,lineManagerEmail, squadGroupName, lineDisplayName, tribeLeadDisplayName, tribeName


class MnRcaMetrics(db.Model):
    __tablename__ = 'mnrcametricstable'
    JiraIssueId = db.Column('JiraIssueId', db.String(64), primary_key=True)
    JiraIssueParentTaskId = db.Column(db.String(64))
    JiraIssueSummary = db.Column(db.String(512))
    JiraIssueType = db.Column(db.String(64))
    JiraIssueCaseType = db.Column(db.String(64))
    JiraIssueStatus = db.Column(db.String(64))
    JiraIssueParentStatus = db.Column(db.String(64))
    JiraIssueAssignee = db.Column(db.String(128))
    JiraIssueReporter = db.Column(db.String(128))
    PRID = db.Column(db.String(64))
    FAID = db.Column(db.String(64))
    PRTitle = db.Column(db.String(1024))
    PRRcaEdaAssessor = db.Column(db.String(128))
    PRAttached = db.Column(db.String(512))
    PRSeverity = db.Column(db.String(32))
    PRGroupInCharge = db.Column(db.String(64))
    JiraIssueCreatedDate = db.Column(db.String(64))
    JiraIssueParentCreatedDate = db.Column(db.String(64))
    JiraIssueResolutionDate = db.Column(db.String(64))
    JiraIssueParentResolutionDate = db.Column(db.String(64))
    JiraIssueDueDate = db.Column(db.String(64))
    JiraIssueOpenDays = db.Column(db.Integer)
    JiraIssueParentOpenDays = db.Column(db.Integer)
    JiraIssueAssigneeSquadGroup = db.Column(db.String(64))
    JiraIssueAssigneeSquadGroupLead = db.Column(db.String(64))
    JiraIssueAssigneeTribe = db.Column(db.String(64))
    JiraIssueAssigneeTribeLead = db.Column(db.String(64))
    JiraIssueOverDue = db.Column(db.String(32))
    JiraIssueParentOverDue = db.Column(db.String(32))
    JiraIssueOverDueReason = db.Column(db.String(1024))
    JiraIssueParentOverDueReason = db.Column(db.String(1024))
    ReportedBy = db.Column(db.String(64))

    def __init__(self, JiraIssueId,JiraIssueParentTaskId,JiraIssueSummary,JiraIssueType,JiraIssueCaseType,\
                 JiraIssueStatus,JiraIssueParentStatus,JiraIssueAssignee,JiraIssueReporter,PRID,FAID,PRTitle,\
                 PRRcaEdaAssessor,PRAttached,PRSeverity,PRGroupInCharge,JiraIssueCreatedDate,JiraIssueParentCreatedDate,\
                 JiraIssueResolutionDate,JiraIssueParentResolutionDate,JiraIssueDueDate,JiraIssueOpenDays,\
                 JiraIssueParentOpenDays,JiraIssueAssigneeSquadGroup,JiraIssueAssigneeSquadGroupLead,\
                 JiraIssueAssigneeTribe,JiraIssueAssigneeTribeLead,JiraIssueOverDue,JiraIssueParentOverDue,\
                 JiraIssueOverDueReason,JiraIssueParentOverDueReason,ReportedBy):

        self.JiraIssueId = JiraIssueId
        self.JiraIssueParentTaskId = JiraIssueParentTaskId
        self.JiraIssueSummary = JiraIssueSummary
        self.JiraIssueType = JiraIssueType
        self.JiraIssueCaseType = JiraIssueCaseType
        self.JiraIssueStatus = JiraIssueStatus
        self.JiraIssueParentStatus = JiraIssueParentStatus
        self.JiraIssueAssignee = JiraIssueAssignee
        self.JiraIssueReporter = JiraIssueReporter
        self.PRID = PRID
        self.FAID = FAID
        self.PRTitle = PRTitle
        self.PRRcaEdaAssessor = PRRcaEdaAssessor
        self.PRAttached = PRAttached
        self.PRSeverity = PRSeverity
        self.PRGroupInCharge = PRGroupInCharge
        self.JiraIssueCreatedDate = JiraIssueCreatedDate
        self.JiraIssueParentCreatedDate = JiraIssueParentCreatedDate
        self.JiraIssueResolutionDate = JiraIssueResolutionDate
        self.JiraIssueParentResolutionDate = JiraIssueParentResolutionDate
        self.JiraIssueDueDate = JiraIssueDueDate
        self.JiraIssueOpenDays = JiraIssueOpenDays
        self.JiraIssueParentOpenDays = JiraIssueParentOpenDays
        self.JiraIssueAssigneeSquadGroup = JiraIssueAssigneeSquadGroup
        self.JiraIssueAssigneeSquadGroupLead = JiraIssueAssigneeSquadGroupLead
        self.JiraIssueAssigneeTribe = JiraIssueAssigneeTribe
        self.JiraIssueAssigneeTribeLead = JiraIssueAssigneeTribeLead
        self.JiraIssueOverDue = JiraIssueOverDue
        self.JiraIssueParentOverDue = JiraIssueParentOverDue
        self.JiraIssueOverDueReason = JiraIssueOverDueReason
        self.JiraIssueParentOverDueReason = JiraIssueParentOverDueReason
        self.ReportedBy = ReportedBy


class Todo(db.Model):
    __tablename__ = 'rcastatus'
    PRID = db.Column('PRID', db.String(64), primary_key=True)
    PRTitle = db.Column(db.String(1024))
    PRReportedDate = db.Column(db.String(64))
    PRClosedDate=db.Column(db.String(64))
    PROpenDays=db.Column(db.Integer)
    PRRcaCompleteDate = db.Column(db.String(64))
    PRRelease = db.Column(db.String(128))
    PRAttached = db.Column(db.String(128))
    IsLongCycleTime = db.Column(db.String(32))
    IsCatM = db.Column(db.String(32))
    IsRcaCompleted = db.Column(db.String(32))
    NoNeedDoRCAReason = db.Column(db.String(64))
    RootCauseCategory=db.Column(db.String(1024))
    FunctionArea = db.Column(db.String(1024))
    CodeDeficiencyDescription = db.Column(db.String(2048))
    CorrectionDescription=db.Column(db.String(1024))
    RootCause = db.Column(db.String(1024))
    IntroducedBy = db.Column(db.String(128))
    Handler = db.Column(db.String(64))

    # New added field for JIRA deployment
    LteCategory=db.Column(db.String(32))
    CustomerOrInternal = db.Column(db.String(32))
    JiraFunctionArea=db.Column(db.String(32))
    TriggerScenarioCategory = db.Column(db.String(128))
    FirstFaultEcapePhase=db.Column(db.String(32))
    FaultIntroducedRelease = db.Column(db.String(256))
    TechnicalRootCause = db.Column(db.String(1024))
    TeamAssessor = db.Column(db.String(64))
    EdaCause = db.Column(db.String(1024))
    RcaRootCause5WhyAnalysis = db.Column(db.String(2048))
    JiraRcaBeReqested = db.Column(db.String(32))
    JiraIssueStatus = db.Column(db.String(32))
    JiraIssueAssignee = db.Column(db.String(128))
    JiraRcaPreparedQualityRating = db.Column(db.Integer)
    JiraRcaDeliveryOnTimeRating = db.Column(db.Integer)
    RcaSubtaskJiraId = db.Column(db.String(32))
    ShouldHaveBeenDetected = db.Column(db.String(128))
    rcaDueDate = db.Column(db.String(64))
    # End of new added field for JIRA

    PRSeverity = db.Column(db.String(32))
    PRGroupInCharge = db.Column(db.String(64))
    PRProduct = db.Column(db.String(64))
    ReportedBy = db.Column(db.String(64))
    FaultCoordinator = db.Column(db.String(64))
    CustomerName = db.Column(db.String(128))
    Feature = db.Column(db.String(128))
    JiraCustomerName = db.Column(db.String(128))
    JIRAProject = db.Column(db.String(128))
    EdaJiraIssueAssignee = db.Column(db.String(128))
    EdaSubtaskJiraId = db.Column(db.String(32))
    edaDueDate = db.Column(db.String(64))
    EdaJiraIssueStatus = db.Column(db.String(32))


    def __init__(self, PRID,PRTitle,PRReportedDate,PRClosedDate,PROpenDays,PRRcaCompleteDate,PRRelease,PRAttached,IsLongCycleTime,\
                 IsCatM,IsRcaCompleted,NoNeedDoRCAReason,RootCauseCategory,FunctionArea,CodeDeficiencyDescription,\
		 CorrectionDescription,RootCause,IntroducedBy,Handler,LteCategory,CustomerOrInternal,JiraFunctionArea,TriggerScenarioCategory, \
                 FirstFaultEcapePhase,FaultIntroducedRelease,TechnicalRootCause,TeamAssessor,EdaCause,RcaRootCause5WhyAnalysis, \
                 JiraRcaBeReqested,JiraIssueStatus,JiraIssueAssignee,JiraRcaPreparedQualityRating,\
                 JiraRcaDeliveryOnTimeRating,RcaSubtaskJiraId,ShouldHaveBeenDetected,rcaDueDate,PRSeverity,PRGroupInCharge, \
                 PRProduct,ReportedBy,FaultCoordinator,CustomerName,Feature,JiraCustomerName,JIRAProject,EdaJiraIssueAssignee,\
                 EdaSubtaskJiraId,edaDueDate,EdaJiraIssueStatus):
        self.PRID = PRID
        self.PRTitle = PRTitle
        self.PRReportedDate = PRReportedDate
        self.PRClosedDate = PRClosedDate
        self.PROpenDays = PROpenDays
        self.PRRcaCompleteDate = PRRcaCompleteDate
        self.PRRelease = PRRelease
        self.PRAttached = PRAttached
        self.IsLongCycleTime = IsLongCycleTime
        self.IsCatM = IsCatM
        self.IsRcaCompleted = IsRcaCompleted
        self.NoNeedDoRCAReason = NoNeedDoRCAReason
        self.RootCauseCategory = RootCauseCategory
        self.FunctionArea = FunctionArea
        self.CodeDeficiencyDescription = CodeDeficiencyDescription
        self.CorrectionDescription = CorrectionDescription
        self.RootCause = RootCause
        self.IntroducedBy = IntroducedBy
        self.Handler = Handler

        # New added for JIRA
        self.LteCategory = LteCategory
        self.CustomerOrInternal = CustomerOrInternal
        self.JiraFunctionArea = JiraFunctionArea
        self.TriggerScenarioCategory = TriggerScenarioCategory
        self.FirstFaultEcapePhase = FirstFaultEcapePhase
        self.FaultIntroducedRelease = FaultIntroducedRelease
        self.TechnicalRootCause = TechnicalRootCause
        self.TeamAssessor = TeamAssessor
        self.EdaCause = EdaCause
        self.RcaRootCause5WhyAnalysis = RcaRootCause5WhyAnalysis
        self.JiraRcaBeReqested = JiraRcaBeReqested
        self.JiraIssueStatus = JiraIssueStatus
        self.JiraIssueAssignee = JiraIssueAssignee
        self.JiraRcaPreparedQualityRating = JiraRcaPreparedQualityRating
        self.JiraRcaDeliveryOnTimeRating = JiraRcaDeliveryOnTimeRating
        self.RcaSubtaskJiraId = RcaSubtaskJiraId
        self.ShouldHaveBeenDetected = ShouldHaveBeenDetected
        self.rcaDueDate = rcaDueDate
        # End of new added field for JIRA
        self.PRSeverity = PRSeverity
        self.PRGroupInCharge = PRGroupInCharge
        self.PRProduct = PRProduct
        self.ReportedBy = ReportedBy
        self.FaultCoordinator = FaultCoordinator
        self.CustomerName = CustomerName
        self.Feature = Feature
        self.JiraCustomerName = JiraCustomerName
        self.JIRAProject = JIRAProject
        self.EdaJiraIssueAssignee = EdaJiraIssueAssignee
        self.EdaSubtaskJiraId = EdaSubtaskJiraId
        self.edaDueDate = edaDueDate
        self.EdaJiraIssueStatus = EdaJiraIssueStatus



def updateEdaInfo(PRID,newissue,EDA_AssessorEmail,edaDueDate):
    # count = Todo.query.all()
    # todos = Todo.query.filter(Todo.JIRAProject != '').order_by(Todo.PRClosedDate.desc()).all()
    todo_item1 = Todo.query.get(PRID)
    if todo_item1:
        todo_item1.EdaJiraIssueAssignee = EDA_AssessorEmail
        todo_item1.EdaSubtaskJiraId = newissue.key
        todo_item1.edaDueDate = edaDueDate
        todo_item1.EdaJiraIssueStatus = str(newissue.fields.status)
        db.session.commit()


JiraUserName = 'rcashark'
# JiraPassWord= 'Jira1234'
JiraPassWord= 'Jira4321'
def getjira():
    options = {'server': 'https://jiradc.int.net.nokia.com/'}
    options = {'server': 'https://jiradc.ext.net.nokia.com/'}
    _conn_status = True
    _conn_retry_count = 0
    while _conn_status:
        try:
            _conn_status = False
            print 'Connecting JIRA...'
            jira = JIRA(options, basic_auth=(JiraUserName, JiraPassWord))
            # return jira
        except:
            _conn_retry_count += 1
            print ("_conn_retry_count=%d" % _conn_retry_count)
            _conn_status = True
            print 'ProntoDb connecting Error'
            time.sleep(10)
        if _conn_status:
            continue
        else:
            print 'Connecting JIRA...OK'
            return jira


if __name__ == '__main__':
    # j = getjira()
    # MnRcaEdaCheckAndAssign(j)

    upload_sharepoint('01309318')





