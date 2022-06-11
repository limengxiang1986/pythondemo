# coding:utf-8
# !/usr/bin/env python
import sys

reload(sys)

sys.setdefaultencoding("utf-8")

from datetime import datetime
from flask import Flask, session, request, flash, url_for, redirect, render_template, abort, g, send_from_directory, \
    jsonify
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
from email.utils import parseaddr, formataddr
import smtplib, time, os

from httplib2 import socks
import socket
from jira.client import JIRA

from ua_parser import user_agent_parser

"""
PROXY_TYPE_HTTP=3
socks.setdefaultproxy(3,"10.144.1.10",8080)
socket.socket = socks.socksocket
"""

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost:3306/fddrca?charset=utf8'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = 'secret_key'
app.config['DEBUG'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# teams=  ['chenlong','xiezhen','yangjinyong','zhangyijie','lanshenghai','liumingjing','lizhongyuan','caizhichao','hujun','wangli']
teams = ['chenlong', 'zhaoli','zhangyijie', 'lanshenghai', 'liumingjing', 'lizhongyuan', \
         'shanlulu','jinguojie','zhuofei.chen@nokia-sbell.com','maciej.1.sikorski@nokia.com']

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column('user_id', db.Integer, primary_key=True)
    username = db.Column('username', db.String(20), unique=True, index=True)
    password = db.Column('password', db.String(250))
    email = db.Column('email', db.String(50), unique=True, index=True)
    registered_on = db.Column('registered_on', db.DateTime)
    todos = db.relationship('Todo', backref='user', lazy='select')
    todoaps = db.relationship('TodoAP', backref='user', lazy='select')
    todolongcycletimercas = db.relationship('TodoLongCycleTimeRCA', backref='user', lazy='select')
    inchargegroups = db.relationship('InChargeGroup', backref='user', lazy='select')

    def __init__(self, username, password, email):
        self.username = username
        self.set_password(password)
        self.email = email
        # self.registered_on = datetime.utcnow()
        self.registered_on = datetime.datetime.now()

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % (self.username)


class JiraUser(db.Model):
    __tablename__ = "jirausers"
    id = db.Column('user_id', db.Integer, primary_key=True)
    username = db.Column('username', db.String(64), unique=True, index=True)
    password = db.Column('password', db.String(256))
    email = db.Column('email', db.String(128), unique=True, index=True)
    displayName = db.Column(db.String(128))
    lineManagerAccountId = db.Column(db.String(128))  # nsnManagerAccountName
    lineManagerDisplayName = db.Column(db.String(128))  # nsnManagerName
    lineManagerEmail = db.Column(db.String(128))  # Further search thru uid.
    squadGroupName = db.Column(db.String(128))  # Further search thru uid.
    registered_on = db.Column('registered_on', db.DateTime)

    todos = db.relationship('Todo', backref='jirauser', lazy='select')
    jiratodos = db.relationship('JiraTodo', backref='jirauser', lazy='select')
    todoaps = db.relationship('TodoAP', backref='jirauser', lazy='select')
    inchargegroups = db.relationship('InChargeGroup', backref='jirauser', lazy='select')

    def __init__(self, username, email, displayName, lineManagerAccountId, lineManagerDisplayName, lineManagerEmail,
                 squadGroupName):
        self.username = username
        self.email = email
        self.displayName = displayName
        self.lineManagerAccountId = lineManagerAccountId
        self.lineManagerDisplayName = lineManagerDisplayName
        self.lineManagerEmail = lineManagerEmail
        self.squadGroupName = squadGroupName
        self.registered_on = datetime.datetime.now()  # datetime.utcnow()

    @staticmethod
    def try_login(username, password):
        global gSSOPWD
        try:
            conn = get_ldap_connection()
        except:
            flash('LDAP Connection Failed!!!')
            return redirect(url_for('login'))
            # return render_template('login.html')
        # app.config['ldap'] = conn
        filter = '(uid=%s)' % username
        attrs = ['sn', 'mail', 'cn', 'displayName', 'nsnManagerAccountName', 'nsnOperativeOrgName']
        base_dn = 'o=NSN'
        try:
            result = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)
        except:
            flash('LDAP Searching Failed!!!')
            return redirect(url_for('login'))
        dn = result[0][0]
        try:
            a = conn.simple_bind_s(dn, password)
            gSSOPWD = password  # For privacy policy, cannot save this for other purpose.
            print 'Cookie auto login or Manual login?????'
        except ldap.INVALID_CREDENTIALS:
            print "Your  password is incorrect!!!"
            flash('Password is incorrect!!')
            return redirect(url_for('login'))
            # sys.exit()
        except ldap.LDAPError, e:
            if type(e.message) == dict and e.message.has_key('desc'):
                print e.message['desc']
            else:
                print e
            # sys.exit()
            flash('LDAP Bind Failed!!!')
            return redirect(url_for('login'))
        except:
            flash('Other reason login Failed!!!')
            return redirect(url_for('login'))
        return result, conn

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<JiraUser %r>' % (self.username)


class Todo(db.Model):
    __tablename__ = 'rcastatus'
    PRID = db.Column('PRID', db.String(64), primary_key=True)
    PRTitle = db.Column(db.String(1024))
    PRReportedDate = db.Column(db.String(64))
    PRClosedDate = db.Column(db.String(64))
    PROpenDays = db.Column(db.Integer)
    PRRcaCompleteDate = db.Column(db.String(64))
    PRRelease = db.Column(db.String(128))
    PRAttached = db.Column(db.String(128))
    IsLongCycleTime = db.Column(db.String(32))
    IsCatM = db.Column(db.String(32))
    IsRcaCompleted = db.Column(db.String(32))
    NoNeedDoRCAReason = db.Column(db.String(64))
    RootCauseCategory = db.Column(db.String(1024))
    FunctionArea = db.Column(db.String(1024))
    CodeDeficiencyDescription = db.Column(db.String(1024))
    CorrectionDescription = db.Column(db.String(1024))
    RootCause = db.Column(db.String(1024))
    IntroducedBy = db.Column(db.String(128))
    Handler = db.Column(db.String(64))

    # New added field for JIRA deployment
    LteCategory = db.Column(db.String(32))
    CustomerOrInternal = db.Column(db.String(32))
    JiraFunctionArea = db.Column(db.String(32))
    TriggerScenarioCategory = db.Column(db.String(128))
    FirstFaultEcapePhase = db.Column(db.String(32))
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

    rca5whys = db.relationship('Rca5Why', backref='todo', lazy='select')
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    jirauser_id = db.Column(db.Integer, db.ForeignKey('jirausers.user_id'))

    def __init__(self, PRID, PRTitle, PRReportedDate, PRClosedDate, PROpenDays, PRRcaCompleteDate, PRRelease,
                 PRAttached, IsLongCycleTime, \
                 IsCatM, IsRcaCompleted, NoNeedDoRCAReason, RootCauseCategory, FunctionArea, CodeDeficiencyDescription, \
                 CorrectionDescription, RootCause, IntroducedBy, Handler, LteCategory, CustomerOrInternal,
                 JiraFunctionArea, TriggerScenarioCategory, \
                 FirstFaultEcapePhase, FaultIntroducedRelease, TechnicalRootCause, TeamAssessor, EdaCause,
                 RcaRootCause5WhyAnalysis, \
                 JiraRcaBeReqested, JiraIssueStatus, JiraIssueAssignee, JiraRcaPreparedQualityRating, \
                 JiraRcaDeliveryOnTimeRating, RcaSubtaskJiraId, ShouldHaveBeenDetected, rcaDueDate):
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


# class TodoEda(db.Model):
#     __tablename__ = 'edastatus'
#     PRID = db.Column('PRID', db.String(64), primary_key=True)
#     PRTitle = db.Column(db.String(1024))
#     PRReportedDate = db.Column(db.String(64))
#     PRClosedDate=db.Column(db.String(64))
#     PROpenDays=db.Column(db.Integer)
#     PRRcaCompleteDate = db.Column(db.String(64))
#     PRRelease = db.Column(db.String(128))
#     PRAttached = db.Column(db.String(128))
#     IsLongCycleTime = db.Column(db.String(32))
#     IsCatM = db.Column(db.String(32))
#     IsRcaCompleted = db.Column(db.String(32))
#     NoNeedDoRCAReason = db.Column(db.String(64))
#     RootCauseCategory=db.Column(db.String(1024))
#     FunctionArea = db.Column(db.String(1024))
#     CodeDeficiencyDescription = db.Column(db.String(1024))
#     CorrectionDescription=db.Column(db.String(1024))
#     RootCause = db.Column(db.String(1024))
#     IntroducedBy = db.Column(db.String(128))
#     Handler = db.Column(db.String(64))
#
#     # New added field for JIRA deployment
#     LteCategory=db.Column(db.String(32))
#     CustomerOrInternal = db.Column(db.String(32))
#     JiraFunctionArea=db.Column(db.String(32))
#     TriggerScenarioCategory = db.Column(db.String(128))
#     FirstFaultEcapePhase=db.Column(db.String(32))
#     FaultIntroducedRelease = db.Column(db.String(256))
#     TechnicalRootCause = db.Column(db.String(1024))
#     TeamAssessor = db.Column(db.String(64))
#     EdaCause = db.Column(db.String(1024))
#     RcaRootCause5WhyAnalysis = db.Column(db.String(2048))
#     JiraRcaBeReqested = db.Column(db.String(32))
#     JiraIssueStatus = db.Column(db.String(32))
#     JiraIssueAssignee = db.Column(db.String(128))
#     JiraRcaPreparedQualityRating = db.Column(db.Integer)
#     JiraRcaDeliveryOnTimeRating = db.Column(db.Integer)
#     RcaSubtaskJiraId = db.Column(db.String(32))
#     # End of new added field for JIRA
#     RcaEdaTribeName = db.Column(db.String(32))
#
#     user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
#
#     def __init__(self, PRID,PRTitle,PRReportedDate,PRClosedDate,PROpenDays,PRRcaCompleteDate,PRRelease,PRAttached,IsLongCycleTime,\
#                  IsCatM,IsRcaCompleted,NoNeedDoRCAReason,RootCauseCategory,FunctionArea,CodeDeficiencyDescription,\
# 		 CorrectionDescription,RootCause,IntroducedBy,Handler,LteCategory,CustomerOrInternal,JiraFunctionArea,TriggerScenarioCategory, \
#                  FirstFaultEcapePhase,FaultIntroducedRelease,TechnicalRootCause,TeamAssessor,EdaCause,RcaRootCause5WhyAnalysis, \
#                  JiraRcaBeReqested,JiraIssueStatus,JiraIssueAssignee,JiraRcaPreparedQualityRating,JiraRcaDeliveryOnTimeRating,RcaSubtaskJiraId,RcaEdaTribeName):
#         self.PRID = PRID
#         self.PRTitle = PRTitle
#         self.PRReportedDate = PRReportedDate
#         self.PRClosedDate = PRClosedDate
#         self.PROpenDays = PROpenDays
#         self.PRRcaCompleteDate = PRRcaCompleteDate
#         self.PRRelease = PRRelease
#         self.PRAttached = PRAttached
#         self.IsLongCycleTime = IsLongCycleTime
#         self.IsCatM = IsCatM
#         self.IsRcaCompleted = IsRcaCompleted
#         self.NoNeedDoRCAReason = NoNeedDoRCAReason
#         self.RootCauseCategory = RootCauseCategory
#         self.FunctionArea = FunctionArea
#         self.CodeDeficiencyDescription = CodeDeficiencyDescription
#         self.CorrectionDescription = CorrectionDescription
#         self.RootCause = RootCause
#         self.IntroducedBy = IntroducedBy
#         self.Handler = Handler
#
#         # New added for JIRA
#         self.LteCategory = LteCategory
#         self.CustomerOrInternal = CustomerOrInternal
#         self.JiraFunctionArea = JiraFunctionArea
#         self.TriggerScenarioCategory = TriggerScenarioCategory
#         self.FirstFaultEcapePhase = FirstFaultEcapePhase
#         self.FaultIntroducedRelease = FaultIntroducedRelease
#         self.TechnicalRootCause = TechnicalRootCause
#         self.TeamAssessor = TeamAssessor
#         self.EdaCause = EdaCause
#         self.RcaRootCause5WhyAnalysis = RcaRootCause5WhyAnalysis
#         self.JiraRcaBeReqested = JiraRcaBeReqested
#         self.JiraIssueStatus = JiraIssueStatus
#         self.JiraIssueAssignee = JiraIssueAssignee
#         self.JiraRcaPreparedQualityRating = JiraRcaPreparedQualityRating
#         self.JiraRcaDeliveryOnTimeRating = JiraRcaDeliveryOnTimeRating
#         self.RcaSubtaskJiraId = RcaSubtaskJiraId
#         # End of new added field for JIRA
#         self.RcaEdaTribeName = RcaEdaTribName

class TodoAP(db.Model):
    __tablename__ = 'apstatus'
    APID = db.Column('APID', db.String(64), primary_key=True)
    PRID = db.Column(db.String(64))
    APDescription = db.Column(db.String(1024))
    APCreatedDate = db.Column(db.String(64))
    APDueDate = db.Column(db.String(64))
    APCompletedOn = db.Column(db.String(64))
    IsApCompleted = db.Column(db.String(32))
    APAssingnedTo = db.Column(db.String(128))
    QualityOwner = db.Column(db.String(128))

    # New added for JIRA
    InjectionRootCauseEdaCause = db.Column(db.String(1024))
    RcaEdaCauseType = db.Column(db.String(128))
    RcaEdaActionType = db.Column(db.String(128))
    TargetRelease = db.Column(db.String(128))
    CustomerAp = db.Column(db.String(32))
    ApCategory = db.Column(db.String(32))  # RCA/EDA
    ShouldHaveBeenDetected = db.Column(db.String(128))
    ApJiraId = db.Column(db.String(32))  # JIRA ID
    # End of added new field for JIRA

    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    jirauser_id = db.Column(db.Integer, db.ForeignKey('jirausers.user_id'))

    def __init__(self, APID, PRID, APDescription, APCreatedDate, APDueDate, APCompletedOn, IsApCompleted, APAssingnedTo,
                 QualityOwner, \
                 InjectionRootCauseEdaCause, RcaEdaCauseType, RcaEdaActionType, TargetRelease, CustomerAp, ApCategory, \
                 ShouldHaveBeenDetected, ApJiraId):
        self.APID = APID
        self.PRID = PRID
        self.APDescription = APDescription
        self.APCreatedDate = APCreatedDate
        self.APDueDate = APDueDate
        self.APCompletedOn = APCompletedOn
        self.IsApCompleted = IsApCompleted
        self.APAssingnedTo = APAssingnedTo
        self.QualityOwner = QualityOwner

        # New added field for JIRA
        self.InjectionRootCauseEdaCause = InjectionRootCauseEdaCause
        self.RcaEdaCauseType = RcaEdaCauseType
        self.RcaEdaActionType = RcaEdaActionType
        self.TargetRelease = TargetRelease
        self.CustomerAp = CustomerAp
        self.ApCategory = ApCategory  # RCA/EDA
        self.ShouldHaveBeenDetected = ShouldHaveBeenDetected
        self.ApJiraId = ApJiraId
        # JIRA End

    # user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))


class Rca5Why(db.Model):
    __tablename__ = 'rca5why'
    id = db.Column('why_id', db.Integer, primary_key=True)
    PRID = db.Column(db.String(64))
    Why1 = db.Column(db.String(1024))
    Why2 = db.Column(db.String(1024))
    Why3 = db.Column(db.String(1024))
    Why4 = db.Column(db.String(1024))
    Why5 = db.Column(db.String(1024))
    pr_id = db.Column(db.String(64), db.ForeignKey('rcastatus.PRID'))

    def __init__(self, PRID, Why1, Why2, Why3, Why4, Why5):
        self.PRID = PRID
        self.Why1 = Why1
        self.Why2 = Why2
        self.Why3 = Why3
        self.Why4 = Why4
        self.Why5 = Why5
        # pr_id = db.Column(db.String(64), db.ForeignKey('rcastatus.PRID'))


class TodoLongCycleTimeRCA(db.Model):
    __tablename__ = 'longcycletimercastatus'
    PRID = db.Column('PRID', db.String(64), primary_key=True)
    PRTitle = db.Column(db.String(1024))
    PRReportedDate = db.Column(db.String(64))
    PRClosedDate = db.Column(db.String(64))
    PROpenDays = db.Column(db.Integer)
    PRRcaCompleteDate = db.Column(db.String(64))
    IsLongCycleTime = db.Column(db.String(32))
    IsCatM = db.Column(db.String(32))
    LongCycleTimeRcaIsCompleted = db.Column(db.String(32))
    LongCycleTimeRootCause = db.Column(db.String(1024))
    NoNeedDoRCAReason = db.Column(db.String(64))
    Handler = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))

    def __init__(self, PRID, PRTitle, PRReportedDate, PRClosedDate, PROpenDays, PRRcaCompleteDate, IsLongCycleTime, \
                 IsCatM, LongCycleTimeRcaIsCompleted, LongCycleTimeRootCause, NoNeedDoRCAReason, Handler):
        self.PRID = PRID
        self.PRTitle = PRTitle
        self.PRReportedDate = PRReportedDate
        self.PRClosedDate = PRClosedDate
        self.PRRcaCompleteDate = PRRcaCompleteDate
        self.PROpenDays = PROpenDays
        self.IsLongCycleTime = IsLongCycleTime
        self.IsCatM = IsCatM
        self.LongCycleTimeRcaIsCompleted = LongCycleTimeRcaIsCompleted
        self.LongCycleTimeRootCause = LongCycleTimeRootCause
        self.NoNeedDoRCAReason = NoNeedDoRCAReason
        self.Handler = Handler


class TodoJiraRcaPreparedQualityRating(db.Model):
    __tablename__ = 'jirarcaqualityrating'
    id = db.Column('rating_id', db.Integer, primary_key=True)
    PRID = db.Column(db.String(64))
    RatingValue = db.Column(db.Integer)
    RatingComments = db.Column(db.String(128))

    def __init__(self, PRID, RatingValue, RatingComments):
        self.PRID = PRID
        self.RatingValue = RatingValue
        self.RatingComments = RatingComments

    """
    Facts collection prepared is not good
    Technical Analysis prepared is not good
    RCA analysis prepared is not good
    EDA analysis prepared is not good
    Two or more item prepared is not good
    Three or more item prepared is not good
    All of the analysis prepared is not good


    """


class SystemLog(db.Model):
    __tablename__ = 'syslog'
    id = db.Column('Index', db.Integer, primary_key=True)
    loginAccount = db.Column(db.String(64), default='')
    loginLocation = db.Column(db.String(128), default='')
    ipAddress = db.Column(db.String(128), default='')
    browserType = db.Column(db.String(128), default='')
    deviceType = db.Column(db.String(128), default='')
    osType = db.Column(db.String(128), default='')
    operationType = db.Column(db.String(128), default='')
    logTime = db.Column(db.DateTime)
    prIdorApId = db.Column(db.String(128), default='')
    log1 = db.Column(db.String(1024), default='')
    log2 = db.Column(db.String(1024), default='')
    log3 = db.Column(db.String(1024), default='')
    log4 = db.Column(db.String(1024), default='')
    log5 = db.Column(db.String(1024), default='')
    log6 = db.Column(db.String(1024), default='')
    log7 = db.Column(db.String(1024), default='')
    log8 = db.Column(db.String(1024), default='')
    log9 = db.Column(db.String(1024), default='')
    log10 = db.Column(db.String(1024), default='')
    log11 = db.Column(db.String(1024), default='')
    log12 = db.Column(db.String(1024), default='')

    def __init__(self, loginAccount, loginLocation, ipAddress, browserType, deviceType, osType, operationType,
                 prIdorApId, \
                 log1, log2, log3, log4, log5, log6, log7, log8, log9, log10, log11, log12):
        self.loginAccount = loginAccount
        self.loginLocation = loginLocation
        self.ipAddress = ipAddress
        self.browserType = browserType
        self.deviceType = deviceType
        self.osType = osType
        self.operationType = operationType
        self.logTime = datetime.datetime.utcnow()
        self.prIdorApId = prIdorApId
        self.log1 = log1
        self.log2 = log2
        self.log3 = log3
        self.log4 = log4
        self.log5 = log5
        self.log6 = log6
        self.log7 = log7
        self.log8 = log8
        self.log9 = log9
        self.log10 = log10
        self.log11 = log11
        self.log12 = log12


class JiraTodo(db.Model):
    __tablename__ = 'jirarcatable1'
    JiraIssueId = db.Column('JiraIssueId', db.String(64), primary_key=True)
    JiraIssuePriority = db.Column(db.String(64))  # Parent task has, Child task does not have
    JiraIssueSourceList = db.Column(db.String(64))  # Parent task has, Child task does not have
    JiraIssueBusinessUnit = db.Column(db.String(128))  # Parent task has, Child task does not have
    JiraIssueBusinessLine = db.Column(db.String(128))  # Parent task has, Child task does not have
    JiraIssueProductLine = db.Column(db.String(128))  # Parent task has, Child task does not have
    JiraIssueCustomerName = db.Column(db.String(128))  # Parent task has, Child task does not have
    JiraIssueFeature = db.Column(db.String(128))
    JiraIssueFeatureComponent = db.Column(db.String(128))
    JiraIssueOther = db.Column(db.String(256))  # Parent task has, Child task does not have
    JiraIssueType = db.Column(db.String(64))
    JiraIssueCaseType = db.Column(db.String(64))  # Child task has, Parent task does not have
    JiraIssueStatus = db.Column(db.String(64))
    JiraIssueLabels = db.Column(db.String(256))
    JiraIssueAssignee = db.Column(db.String(128))
    JiraIssueReporter = db.Column(db.String(128))
    PRID = db.Column('PRID', db.String(64))
    PRTitle = db.Column(db.String(1024))
    PRRcaEdaAssessor = db.Column(db.String(128))
    PRRelease = db.Column(db.String(128))
    PRAttached = db.Column(db.String(128))
    PRSeverity = db.Column(db.String(32))
    PRGroupInCharge = db.Column(db.String(64))
    PRProduct = db.Column(db.String(64))
    ReportedBy = db.Column(db.String(64))
    FaultCoordinator = db.Column(db.String(64))
    JiraIssueSummary = db.Column(db.String(512))
    CustomerName = db.Column(db.String(128))
    APDueDate = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('jirausers.user_id'))

    def __init__(self, JiraIssueId, JiraIssuePriority, JiraIssueSourceList, JiraIssueBusinessUnit, \
                 JiraIssueBusinessLine, JiraIssueProductLine, JiraIssueCustomerName, JiraIssueFeature,
                 JiraIssueFeatureComponent, \
                 JiraIssueOther, JiraIssueType, JiraIssueCaseType, JiraIssueStatus, JiraIssueLabels, JiraIssueAssignee, \
                 JiraIssueReporter, PRID, PRTitle, PRRelease, PRSeverity, PRGroupInCharge, PRAttached, PRRcaEdaAssessor, \
                 PRProduct, ReportedBy, FaultCoordinator, JiraIssueSummary, CustomerName, APDueDate):
        self.JiraIssueId = JiraIssueId
        self.JiraIssuePriority = JiraIssuePriority
        self.JiraIssueSourceList = JiraIssueSourceList
        self.JiraIssueBusinessUnit = JiraIssueBusinessUnit
        self.JiraIssueBusinessLine = JiraIssueBusinessLine
        self.JiraIssueProductLine = JiraIssueProductLine
        self.JiraIssueCustomerName = JiraIssueCustomerName
        self.JiraIssueFeature = JiraIssueFeature
        self.JiraIssueFeatureComponent = JiraIssueFeatureComponent
        self.JiraIssueOther = JiraIssueOther
        self.JiraIssueType = JiraIssueType
        self.JiraIssueCaseType = JiraIssueCaseType
        self.JiraIssueStatus = JiraIssueStatus
        self.JiraIssueLabels = JiraIssueLabels
        self.JiraIssueAssignee = JiraIssueAssignee
        self.JiraIssueReporter = JiraIssueReporter
        self.PRID = PRID
        self.PRTitle = PRTitle
        self.PRRcaEdaAssessor = PRRcaEdaAssessor
        self.PRRelease = PRRelease
        self.PRAttached = PRAttached
        self.PRSeverity = PRSeverity
        self.PRGroupInCharge = PRGroupInCharge
        self.PRProduct = PRProduct
        self.ReportedBy = ReportedBy
        self.FaultCoordinator = FaultCoordinator
        self.JiraIssueSummary = JiraIssueSummary
        self.CustomerName = CustomerName
        self.APDueDate = APDueDate


class InChargeGroup(db.Model):
    __tablename__ = "inchargegroups4"
    id = db.Column('index', db.Integer)
    InChargeGroupName = db.Column(db.String(128), primary_key=True)
    AssessorEmail = db.Column(db.String(64), index=True)
    AddedBy = db.Column(db.String(64))

    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    jirauser_id = db.Column(db.Integer, db.ForeignKey('jirausers.user_id'))

    def __init__(self, InChargeGroupName, AssessorEmail, AddedBy):
        self.InChargeGroupName = InChargeGroupName
        self.AssessorEmail = AssessorEmail
        self.AddedBy = AddedBy


#db.create_all()
"""
app.config['dbconfig'] = {'host': '127.0.0.1',
                          'user': 'root',
                          'password': '',
                          'database': 'fddrca', }


mysql://10.68.184.123:8080/jupiter4?autoReconnect=true

Database name: jupiter4, Table names: t_boxi_closed_pronto_daily AND t_boxi_new_pronto_daily

User/pwd: root/jupiter111
"""
app.config['dbconfig'] = {'host': '10.68.184.123',
                          'port': 8080,
                          'user': 'root',
                          'password': 'jupiter111',
                          'database': 'jupiter4', }

gAdmin = 'krma'
gAuth = 'Nokia123'
# auth=('krma', 'Nokia123')
class UseDatabase:
    def __init__(self, config):
        self.configuration = config

    def __enter__(self):
        self.conn = mysql.connector.connect(**self.configuration)
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()


class UseDatabaseDict:
    def __init__(self, config):
        """Add the database configuration parameters to the object.

        This class expects a single dictionary argument which needs to assign
        the appropriate values to (at least) the following keys:

            host - the IP address of the host running MySQL/MariaDB.
            user - the MySQL/MariaDB username to use.
            password - the user's password.
            database - the name of the database to use.

        For more options, refer to the mysql-connector-python documentation.
        """
        self.configuration = config

    def __enter__(self):
        """
        Connect to database and create a DB cursor.
            cursor = cnx.cursor(dictionary=True)
            cursor.execute("SELECT * FROM country WHERE Continent = 'Europe'")
        Return the database cursor to the context manager.
        """
        self.conn = mysql.connector.connect(**self.configuration)
        self.cursor = self.conn.cursor(dictionary=True)
        return self.cursor

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Destroy the cursor as well as the connection (after committing).
        """
        self.conn.commit()
        self.cursor.close()
        self.conn.close()


def compare_time(start_t, end_t):
    s_time = time.mktime(time.strptime(start_t, '%Y-%m-%d'))
    # get the seconds for specify date
    e_time = time.mktime(time.strptime(end_t, '%Y-%m-%d'))
    if float(s_time) >= float(e_time):
        return True
    return False


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
    else:
        sum1 = 0
        y1 = year1
        while y1 < year2:
            sum1 += days_this_year(y1)
            y1 += 1
        return sum1 - days_passed(year1, month1, day1) + days_passed(year2, month2, day2)


"""
    ip_set = [int(i) for i in ip_addr.split('.')]
    ip_number = (ip_set[0] << 24) + (ip_set[1] << 16) + (ip_set[2] << 8) + ip_set[3]
    return ip_number
    ext = fname.rsplit('.', 1)[1]

"""


def daysBetweenDate(start, end):
    year1 = int(start.split('-', 2)[0])
    month1 = int(start.split('-', 2)[1])
    day1 = int(start.split('-', 2)[2])

    year2 = int(end.split('-', 2)[0])
    month2 = int(end.split('-', 2)[1])
    day2 = int(end.split('-', 2)[2])
    print ("daysBetweenDates(year1, month1, day1, year2, month2, day2)=%d" % daysBetweenDates(year1, month1, day1,
                                                                                              year2, month2, day2))
    return daysBetweenDates(year1, month1, day1, year2, month2, day2)


def insert_item(team, PRID, PRTitle, PRReportedDate, PRClosedDate, PRRelease, PRAttached, IntroducedBy, TeamAssessor,
                jira):
    PROpenDays = daysBetweenDate(PRReportedDate, PRClosedDate)
    PRRcaCompleteDate = ''
    if daysBetweenDate(PRReportedDate, PRClosedDate) > 14:
        IsLongCycleTime = 'Yes'
    else:
        IsLongCycleTime = 'No'

    IsCatM = ''
    IsRcaCompleted = 'No'
    LongCycleTimeRcaIsCompleted = 'No'
    NoNeedDoRCAReason = ''
    RootCauseCategory = ''
    FunctionArea = ''

    CodeDeficiencyDescription = ''
    CorrectionDescription = ''
    RootCause = ''
    LongCycleTimeRootCause = ''

    IntroducedBy = IntroducedBy
    Handler = team
    # todo_item = Todo.query.get(PRID)

    LteCategory = 'FDD'
    JiraFunctionArea = ''
    TriggerScenarioCategory = ''
    FirstFaultEcapePhase = ''
    FaultIntroducedRelease = ''
    TechnicalRootCause = ''
    TeamAssessor = TeamAssessor
    EdaCause = ''
    RcaRootCause5WhyAnalysis = ''
    status, assignee, RcaSubtaskJiraId = JiraRequest(jira, PRID)
    if status is False:
        CustomerOrInternal = 'No'
        JiraRcaBeReqested = 'No'
        JiraIssueStatus = ''
        JiraIssueAssignee = ''
        JiraRcaPreparedQualityRating = 10
        JiraRcaDeliveryOnTimeRating = 10
        RcaSubtaskJiraId = ''
    else:
        CustomerOrInternal = 'Yes'
        JiraRcaBeReqested = 'Yes'
        JiraIssueAssignee = assignee
        JiraIssueStatus = status
        JiraRcaPreparedQualityRating = 10
        JiraRcaDeliveryOnTimeRating = 10
        RcaSubtaskJiraId = RcaSubtaskJiraId
    registered_user = Todo.query.filter_by(PRID=PRID).all()
    if len(registered_user) == 0:
        todo = Todo(PRID, PRTitle, PRReportedDate, PRClosedDate, PROpenDays, PRRcaCompleteDate, PRRelease, PRAttached,
                    IsLongCycleTime, \
                    IsCatM, IsRcaCompleted, NoNeedDoRCAReason, RootCauseCategory, FunctionArea,
                    CodeDeficiencyDescription, \
                    CorrectionDescription, RootCause, IntroducedBy, Handler, LteCategory, CustomerOrInternal,
                    JiraFunctionArea, TriggerScenarioCategory, \
                    FirstFaultEcapePhase, FaultIntroducedRelease, TechnicalRootCause, TeamAssessor, EdaCause,
                    RcaRootCause5WhyAnalysis, \
                    JiraRcaBeReqested, JiraIssueStatus, JiraIssueAssignee, JiraRcaPreparedQualityRating,
                    JiraRcaDeliveryOnTimeRating, \
                    RcaSubtaskJiraId)

        hello = User.query.filter_by(username=team).first()
        todo.user_id = hello.id
        print("todo.user_id=hello.user_id=%s" % hello.id)
        db.session.add(todo)
        db.session.commit()
    else:
        todo_item = Todo.query.get(PRID)
        todo_item.IntroducedBy = IntroducedBy
        todo_item.Handler = Handler
        todo_item.CustomerOrInternal = CustomerOrInternal
        todo_item.JiraRcaBeReqested = JiraRcaBeReqested
        todo_item.LteCategory = LteCategory
        todo_item.JiraRcaBeReqested = JiraRcaBeReqested
        todo_item.TeamAssessor = TeamAssessor
        todo_item.JiraIssueStatus = JiraIssueStatus
        todo_item.JiraIssueAssignee = JiraIssueAssignee
        # todo_item.JiraIssueAssignee = JiraIssueAssignee
        todo_item.RcaSubtaskJiraId = RcaSubtaskJiraId

        count = TodoJiraRcaPreparedQualityRating.query.filter_by(PRID=PRID).count()
        values = TodoJiraRcaPreparedQualityRating.query.filter_by(PRID=PRID).all()
        sum = 0

        if count != 0:
            for item in values:
                sum = sum + item.RatingValue
            todo_item.JiraRcaPreparedQualityRating = sum / count
        else:
            todo_item.JiraRcaPreparedQualityRating = 10

        current_time = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        dayspast = daysBetweenDate(PRClosedDate, current_time)

        with UseDatabaseDict(app.config['dbconfig']) as cursor:
            _SQL = "select * from user_info where displayName = '" + JiraIssueAssignee + "'"
            cursor.execute(_SQL)
            items = cursor.fetchall()
        if len(items) != 0:
            if JiraIssueStatus in ['Open', 'Reopened', 'In Progress'] and JiraRcaBeReqested == 'Yes':
                todo_item.IsRcaCompleted = 'No'
                if dayspast <= 14:
                    todo_item.JiraRcaDeliveryOnTimeRating = 10
                else:
                    todo_item.JiraRcaDeliveryOnTimeRating = 24 - dayspast
            elif JiraIssueStatus in ['Closed', 'Resolved']:
                todo_item.IsRcaCompleted = 'Yes'
        db.session.commit()
        print ("registered_user.PRTitle=%s" % PRID)

    registered_user = TodoLongCycleTimeRCA.query.filter_by(PRID=PRID).all()
    if len(registered_user) == 0 and IsLongCycleTime == 'Yes':
        print 'OK#################################################'
        todo = TodoLongCycleTimeRCA(PRID, PRTitle, PRReportedDate, PRClosedDate, PROpenDays, PRRcaCompleteDate,
                                    IsLongCycleTime, \
                                    IsCatM, LongCycleTimeRcaIsCompleted, LongCycleTimeRootCause, NoNeedDoRCAReason,
                                    Handler)

        hello = User.query.filter_by(username=team).first()
        todo.user_id = hello.id
        print("todo.user_id=hello.user_id=%s" % hello.id)
        db.session.add(todo)
        db.session.commit()
    elif IsLongCycleTime == 'Yes':
        todo_item = TodoLongCycleTimeRCA.query.get(PRID)
        todo_item.Handler = Handler
        hello = User.query.filter_by(username=team).first()
        todo_item.user_id = hello.id
        db.session.commit()
        print ("registered_user.PRTitle=%s" % PRID)


def reConnectProntoDb():
    _conn_status = True
    _conn_retry_count = 0
    while _conn_status:
        try:
            print 'Connecting Pronto FDD Db...'
            with UseDatabaseDict(app.config['dbconfig']) as cursor:
                _conn_status = False
                # _SQL = "select * from t_boxi_closed_pronto_daily where PRGroupIC='LTE_DEVCAHZ_CHZ_UPMACPS'"
                _SQL = "SELECT DISTINCT prcls.PRID,prcls.PRTitle, prcls.PRGroupIC, prcls.PRRelease, prcls.PRReportedDate, prcls.PRState, \
                    date_format(prcls.ClosedEnter, '%Y-%m-%d') as PRClosedDate,prcls.PRAttached,\
                    prnew.RespPerson FROM t_boxi_closed_pronto_daily as prcls LEFT JOIN t_boxi_new_pronto_daily as prnew\
                    ON prcls.PRID = prnew.PRID WHERE prcls.PRGroupIC in ('LTE_DEVCAHZ_CHZ_UPMACPS','LTE_DEVPFHZ_CHZ_UPMACPS','NIOYSR2','LTE_DEVHZ1_CHZ_SPEC_UP')\
                     and prcls.PRState='Closed'and prcls.ClosedEnter >='2018-01-01' and prcls.identicalFlag='1' and prcls.isFNR='0'"
                cursor.execute(_SQL)
                contents = cursor.fetchall()
                return contents
        except:
            _conn_retry_count += 1
            print ("_conn_retry_count=%d" % _conn_retry_count)
        print 'ProntoDb connecting Error'
        time.sleep(10)
        contiue


def reConnectProntoDbTdd():
    _conn_status = True
    _conn_retry_count = 0
    while _conn_status:
        try:
            print 'Connecting Pronto TDD Db...'
            with UseDatabaseDict(app.config['dbconfig']) as cursor:
                _conn_status = False
                # _SQL = "select * from t_boxi_closed_pronto_daily where PRGroupIC='LTE_DEVCAHZ_CHZ_UPMACPS'"
                _SQL = "SELECT DISTINCT prcls.PRID,prcls.PRTitle, prcls.PRGroupIC, prcls.PRRelease, prcls.PRReportedDate, prcls.PRState, \
                    date_format(prcls.ClosedEnter, '%Y-%m-%d') as PRClosedDate,prcls.PRAttached,\
                    prnew.RespPerson FROM t_boxi_closed_pronto_daily as prcls LEFT JOIN t_boxi_new_pronto_daily as prnew\
                    ON prcls.PRID = prnew.PRID WHERE prcls.PRGroupIC in ('NIHZSMAC','NIHZYSUP')\
                     and prcls.PRState='Closed'and prcls.ClosedEnter >='2018-01-01' and prcls.identicalFlag='1' and prcls.isFNR='0'"
                cursor.execute(_SQL)
                contents = cursor.fetchall()
                return contents
        except:
            _conn_retry_count += 1
            print ("_conn_retry_count=%d" % _conn_retry_count)
        print 'ProntoDb connecting Error'
        time.sleep(10)
        continue


def update_from_tbox(jira):
    # teams=['chenlong','xiezhen','yangjinyong','zhangyijie','lanshenghai','liumingjing','lizhongyuan','caizhichao','hujun','wuyuanxing']
    contents = reConnectProntoDb()
    count = len(contents)
    member_map = {}
    for linename in teams:
        memberlist = []
        members = TodoMember.query.filter_by(lineManager=linename).all()
        for member in members:
            email = member.emailName
            email = email.encode('utf-8').strip()
            memberlist.append(email)
        member_map.setdefault(linename, memberlist)
        print 'before hello'
        for content in contents:
            PRID = content['PRID'].encode('utf-8').strip()
            todo_item = Todo.query.get(PRID)
            """
            if todo_item:
                continue
            """
            RespPerson = []
            resp = content['RespPerson'].encode('utf-8').strip()
            RespPerson = resp_members(resp)
            # RespPerson.append(resp)
            a = list(set(member_map[linename]).intersection(set(RespPerson)))
            memberline = set(RespPerson)
            retA = [val for val in RespPerson if val in member_map[linename]]
            # RespPerson = set(RespPerson)
            # retA = [i for i in listA if i in listB]
            MemberOfLine = set(member_map[linename])
            s = MemberOfLine.intersection(memberline)
            if MemberOfLine.intersection(memberline):
                IntroducedBy = MemberOfLine.intersection(memberline)
                print 'hello'
                PRID = content['PRID'].encode('utf-8').strip()
                print PRID
                PRTitle = content['PRTitle'].encode('utf-8').strip()
                PRReportedDate = str(content['PRReportedDate'])
                PRClosedDate = content['PRClosedDate'].encode('utf-8').strip()
                PRRelease = content['PRRelease'].encode('utf-8').strip()
                PRAttached = content['PRAttached'].encode('utf-8').strip()
                IntroducedBy = IntroducedBy

                if content['PRGroupIC'] == 'NIOYSR2' or content['PRGroupIC'] == 'LTE_DEVHZ1_CHZ_SPEC_UP':
                    TeamAssessor = 'jun-julian.hu@nokia-sbell.com'
                    insert_item('wangli', PRID, PRTitle, PRReportedDate, PRClosedDate, PRRelease, PRAttached,
                                IntroducedBy, TeamAssessor, jira)
                else:
                    TeamAssessor = addr_dict[linename]['fc']
                    insert_item(linename, PRID, PRTitle, PRReportedDate, PRClosedDate, PRRelease, PRAttached,
                                IntroducedBy, \
                                TeamAssessor, jira)

# JiraUserName = 'Ca_AutomationAccount'
# JiraPassWord= 'jira123'
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
            print 'Jira connecting Error...'
            time.sleep(10)
        if _conn_status:
            continue
        else:
            print 'Connecting JIRA...OK'
            return jira


def JiraRequest(jira, PRID):
    JIRA_STATUS = {'Closed', 'Resolved'}
    MNPRCA = 'MNPRCA'
    TYPE = '5WhyRCA'
    issues = jira.search_issues(jql_str='project = MNRCA AND summary~' + PRID + ' AND type = "Analysis subtask"',
                                maxResults=5)
    # issues = jira.search_issues(jql_str='project = MNPRCA AND summary~' + PRID + ' AND type = "5WhyRCA"',maxResults=5)
    if len(issues):
        for issue in issues:
            CaseType = str(issue.fields.customfield_10464)
            if CaseType == 'RCA' or CaseType == 'RCA and EDA':
                status = str(issue.fields.status)
                assignee = str(issue.fields.assignee)
                jiraissuekey = issue.key
                return status, assignee, jiraissuekey
            else:
                continue
    return False, False, False

def jiraRequest1(jira, PRID):
    JIRA_STATUS = {'Closed', 'Resolved'}
    MNPRCA = 'MNPRCA'
    TYPE = '5WhyRCA'
    issues = jira.search_issues(jql_str='project = MNRCA AND summary~' + PRID + ' AND type = "Analysis subtask"',
                                maxResults=5)
    # issues = jira.search_issues(jql_str='project = MNPRCA AND summary~' + PRID + ' AND type = "5WhyRCA"',maxResults=5)
    if len(issues):
        for issue in issues:
            CaseType = str(issue.fields.customfield_10464)
            if CaseType == 'RCA' or CaseType == 'RCA and EDA':
                status = str(issue.fields.status)
                assignee = str(issue.fields.assignee)
                jiraissuekey = issue.key
                rcaDueDate = issue.fields.customfield_27792
                return status, assignee, jiraissuekey,rcaDueDate
            else:
                continue
    return False, False, False,False

def FiveWhyRcaRequestOnly(jira, PRID):
    JIRA_STATUS = {'Closed', 'Resolved'}
    MNPRCA = 'MNPRCA'
    TYPE = '5WhyRCA'
    #issues = jira.search_issues(jql_str='project = MNRCA AND summary~' + PRID + ' AND type = "Analysis subtask"',maxResults=5)
    issues = jira.search_issues(jql_str='project = MNPRCA AND summary~' + PRID + ' AND type = "5WhyRCA" and assignee= mingjliu',maxResults=5)
    if len(issues):
        for issue in issues:
            CaseType = str(issue.fields.customfield_10464)
            if CaseType == 'RCA' or CaseType == 'RCA and EDA':
                status = str(issue.fields.status)
                assignee = str(issue.fields.assignee)
                jiraissuekey = issue.key
                return status, assignee, jiraissuekey
            else:
                continue
                #issue.fields.subtasks
    return False, False, False

def insert_item_jira(team, PRID, PRTitle, PRReportedDate, PRClosedDate, PRRelease, PRAttached, IntroducedBy, \
                     LteCategory, JiraRcaBeReqested, TeamAssessor, JiraIssueStatus, JiraIssueAssignee,
                     RcaSubtaskJiraId):
    PROpenDays = daysBetweenDate(PRReportedDate, PRClosedDate)
    PRRcaCompleteDate = ''
    if daysBetweenDate(PRReportedDate, PRClosedDate) > 14:
        IsLongCycleTime = 'Yes'
    else:
        IsLongCycleTime = 'No'

    IsCatM = ''
    IsRcaCompleted = 'No'
    LongCycleTimeRcaIsCompleted = 'No'
    NoNeedDoRCAReason = ''
    RootCauseCategory = ''
    FunctionArea = ''

    CodeDeficiencyDescription = ''
    CorrectionDescription = ''
    RootCause = ''
    LongCycleTimeRootCause = ''

    IntroducedBy = IntroducedBy
    Handler = team

    LteCategory = LteCategory
    CustomerOrInternal = 'Yes'
    JiraFunctionArea = ''
    TriggerScenarioCategory = ''
    FirstFaultEcapePhase = ''
    FaultIntroducedRelease = ''
    TechnicalRootCause = ''
    TeamAssessor = TeamAssessor
    EdaCause = ''
    RcaRootCause5WhyAnalysis = ''
    JiraRcaBeReqested = JiraRcaBeReqested
    JiraIssueStatus = JiraIssueStatus
    JiraIssueAssignee = JiraIssueAssignee
    JiraRcaPreparedQualityRating = 10
    JiraRcaDeliveryOnTimeRating = 10
    RcaSubtaskJiraId = RcaSubtaskJiraId
    with UseDatabaseDict(app.config['dbconfig']) as cursor:
        # _SQL = "select * from user_info where displayName = '" + JiraIssueAssignee + "'"
        _SQL = "select * from user_info where email = '" + TeamAssessor + "'"
        cursor.execute(_SQL)
        items = cursor.fetchall()
    if len(items) != 0:
        emailname = items[0]['email'].encode('utf-8')
        lmEmail = items[0]['lmEmail'].encode('utf-8')
        if lmEmail in addr_dict1.keys():
            team = addr_dict1[lmEmail]
            # TeamAssessor = emailname
            Handler = team
    # hello = User.query.filter_by(username=Handler).first()
    registered_user = Todo.query.filter_by(PRID=PRID).all()
    if len(registered_user) == 0:
        todo = Todo(PRID, PRTitle, PRReportedDate, PRClosedDate, PROpenDays, PRRcaCompleteDate, PRRelease, PRAttached,
                    IsLongCycleTime, \
                    IsCatM, IsRcaCompleted, NoNeedDoRCAReason, RootCauseCategory, FunctionArea,
                    CodeDeficiencyDescription, \
                    CorrectionDescription, RootCause, IntroducedBy, Handler, LteCategory, CustomerOrInternal,
                    JiraFunctionArea, TriggerScenarioCategory, \
                    FirstFaultEcapePhase, FaultIntroducedRelease, TechnicalRootCause, TeamAssessor, EdaCause,
                    RcaRootCause5WhyAnalysis, \
                    JiraRcaBeReqested, JiraIssueStatus, JiraIssueAssignee, JiraRcaPreparedQualityRating,
                    JiraRcaDeliveryOnTimeRating, \
                    RcaSubtaskJiraId)

        hello = User.query.filter_by(username=Handler).first()
        todo.user_id = hello.id
        print("todo.user_id=hello.user_id=%s" % hello.id)
        db.session.add(todo)
        db.session.commit()
    else:
        todo_item = Todo.query.get(PRID)
        todo_item.IntroducedBy = IntroducedBy
        todo_item.Handler = Handler
        todo_item.LteCategory = LteCategory
        todo_item.CustomerOrInternal = CustomerOrInternal
        todo_item.JiraRcaBeReqested = JiraRcaBeReqested
        todo_item.JiraIssueStatus = JiraIssueStatus
        todo_item.TeamAssessor = TeamAssessor
        todo_item.JiraIssueAssignee = JiraIssueAssignee

        count = TodoJiraRcaPreparedQualityRating.query.filter_by(PRID=PRID).count()
        values = TodoJiraRcaPreparedQualityRating.query.filter_by(PRID=PRID).all()
        sum = 0

        if count != 0:
            for item in values:
                sum = sum + item.RatingValue
            todo_item.JiraRcaPreparedQualityRating = sum / count
        else:
            todo_item.JiraRcaPreparedQualityRating = 10

        current_time = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        dayspast = daysBetweenDate(PRClosedDate, current_time)
        with UseDatabaseDict(app.config['dbconfig']) as cursor:
            SQL = "select * from user_info where displayName = '" + JiraIssueAssignee + "'"
            # _SQL = "select * from user_info where email = '" + TeamAssessor + "'"
            cursor.execute(_SQL)
            items = cursor.fetchall()
            if len(items) != 0:
                if JiraIssueStatus in ['Open', 'Reopened', 'In Progress'] and JiraRcaBeReqested == 'Yes':
                    todo_item.IsRcaCompleted = 'No'
                    if dayspast <= 14:
                        todo_item.JiraRcaDeliveryOnTimeRating = 10
                    else:
                        todo_item.JiraRcaDeliveryOnTimeRating = 24 - dayspast
                elif JiraIssueStatus in ['Closed', 'Resolved']:
                    todo_item.IsRcaCompleted = 'Yes'
        """
            emailname = items[0]['email'].encode('utf-8')
            lmEmail = items[0]['lmEmail'].encode('utf-8')
            if lmEmail in addr_dict1.keys():
                team = addr_dict1[lmEmail]
                #todo_item.TeamAssessor = emailname
                todo_item.Handler = team
        #else:
            #todo_item.IsRcaCompleted = 'Yes'
        hello = User.query.filter_by(username=team).first()
        todo_item.user_id = hello.id
        """
        db.session.commit()
        print ("registered_user.PRTitle=%s" % PRID)

    registered_user = TodoLongCycleTimeRCA.query.filter_by(PRID=PRID).all()
    if len(registered_user) == 0 and IsLongCycleTime == 'Yes':
        print 'OK#################################################'
        todo = TodoLongCycleTimeRCA(PRID, PRTitle, PRReportedDate, PRClosedDate, PROpenDays, PRRcaCompleteDate,
                                    IsLongCycleTime, \
                                    IsCatM, LongCycleTimeRcaIsCompleted, LongCycleTimeRootCause, NoNeedDoRCAReason,
                                    Handler)

        hello = User.query.filter_by(username=team).first()
        todo.user_id = hello.id
        print("todo.user_id=hello.user_id=%s" % hello.id)
        db.session.add(todo)
        db.session.commit()
    elif IsLongCycleTime == 'Yes':
        todo_item = TodoLongCycleTimeRCA.query.get(PRID)
        todo_item.Handler = Handler
        hello = User.query.filter_by(username=team).first()
        todo_item.user_id = hello.id
        db.session.commit()
        print ("registered_user.PRTitle=%s" % PRID)


# FC mapping table
FC_addr_dict = {}
FC_addr_dict['chenlong'] = {'email': 'loong.chen@nokia-sbell.com', 'fc': 'feilu.xiao@nokia-sbell.com'}
FC_addr_dict['yangjinyong'] = {'email': 'jinyong.yang@nokia-sbell.com', 'fc': 'joseph.zhou@nokia-sbell.com'}
FC_addr_dict['zhangyijie'] = {'email': 'yijie.zhang@nokia-sbell.com', 'fc': 'xi-sandy.cheng@nokia-sbell.com'}
FC_addr_dict['lanshenghai'] = {'email': 'shenghai.lan@nokia-sbell.com', 'fc': 'linggang.tu@nokia-sbell.com'}
FC_addr_dict['liumingjing'] = {'email': 'mingjing.liu@nokia-sbell.com', 'fc': 'qinyu.zhao@nokia-sbell.com'}
FC_addr_dict['lizhongyuan'] = {'email': 'zhongyuan.y.li@nokia-sbell.com', 'fc': 'yu.tan@nokia-sbell.com'}
# addr_dict['leienqing']={'email':'enqing.lei@nokia-sbell.com','fc':'chengbin.qi@nokia-sbell.com'}
FC_addr_dict['caizhichao'] = {'email': 'zhi_chao.cai@nokia-sbell.com', 'fc': 'zhi_chao.cai@nokia-sbell.com'}
FC_addr_dict['hujun'] = {'email': 'jun-julian.hu@nokia-sbell.com', 'fc': 'jun-julian.hu@nokia-sbell.com'}
FC_addr_dict['zhaoli'] = {'email': 'li.2.zhao@nokia-sbell.com', 'fc': 'li.2.zhao@nokia-sbell.com'}
FC_addr_dict['wangli'] = {'email': 'li-daniel.wang@nokia-sbell.com','fc': 'jun-julian.hu@nokia-sbell.com'}
FC_addr_dict['zhaoli'] = {'email': 'li.2.zhao@nokia-sbell.com','fc': 'li.2.zhao@nokia-sbell.com'}
FC_addr_dict['jinguojie'] = {'email': 'guojie.jin@nokia-sbell.com','fc': 'jun.3.guo@nokia-sbell.com'}
FC_addr_dict['shanlulu'] = {'email': 'lulu.shan@nokia-sbell.com','fc': 'jun.3.guo@nokia-sbell.com'}
FC_addr_dict['zhuofei.chen@nokia-sbell.com'] = {'email': 'zhuofei.chen@nokia-sbell.com','fc': 'zhuofei.chen@nokia-sbell.com'}
FC_addr_dict['maciej.1.sikorski@nokia.com'] = {'email': 'maciej.1.sikorski@nokia.com','fc': 'maciej.1.sikorski@nokia.com'}

addr_dict1 = {}
addr_dict1['loong.chen@nokia-sbell.com'] = 'chenlong'
addr_dict1['jinyong.yang@nokia-sbell.com'] = 'yangjinyong'
addr_dict1['yijie.zhang@nokia-sbell.com'] = 'zhangyijie'
addr_dict1['shenghai.lan@nokia-sbell.com'] = 'lanshenghai'
addr_dict1['mingjing.liu@nokia-sbell.com'] = 'liumingjing'
addr_dict1['zhongyuan.y.li@nokia-sbell.com'] = 'lizhongyuan'
addr_dict1['zhi_chao.cai@nokia-sbell.com'] = 'caizhichao'
addr_dict1['jason.xie@nokia-sbell.com'] = 'xiezhen'
addr_dict1['li-daniel.wang@nokia-sbell.com'] = 'wangli'
addr_dict1['li.2.zhao@nokia-sbell.com'] = 'zhaoli'
addr_dict1['zhuofei.chen@nokia-sbell.com'] = 'zhuofei.chen@nokia-sbell.com'
addr_dict1['maciej.1.sikorski@nokia.com'] = 'maciej.1.sikorski@nokia.com'


def update_from_tbox_fdd(jira):
    member_map = {}
    contents = reConnectProntoDb()
    for content in contents:
        PRID = content['PRID'].encode('utf-8').strip()
        todo_item = Todo.query.get(PRID)
        # If already in WebApp table, then no need update anymore, keep the manual change valid.
        if todo_item:
            continue
        """
        status,assignee,RcaSubtaskJiraId = JiraRequest(jira,PRID)
        if status is False:
            continue
        JiraIssueStatus = status
        JiraIssueAssignee =assignee
        RcaSubtaskJiraId = RcaSubtaskJiraId
        """
        # JiraIssueStatus = GetJiraIssueStatus(issue)
        for linename in teams:
            email_name = addr_dict[linename]['email']
            with UseDatabaseDict(app.config['dbconfig']) as cursor:
                _SQL = "select * from user_info where lmEmail= '" + email_name + "'"
                cursor.execute(_SQL)
                members = cursor.fetchall()
            memberlist = []
            # members = TodoMember.query.filter_by(lineManager=linename).all()
            for member in members:
                displayname = member['displayName']
                email = displayname.encode('utf-8').strip()
                memberlist.append(email)
            member_map.setdefault(linename, memberlist)
            print 'before hello'
            resp = content['RespPerson'].encode('utf-8').strip()
            RespPerson = resp_members(resp)
            a = list(set(member_map[linename]).intersection(set(RespPerson)))
            memberline = set(RespPerson)
            retA = [val for val in RespPerson if val in member_map[linename]]
            MemberOfLine = set(member_map[linename])
            s = MemberOfLine.intersection(memberline)
            if MemberOfLine.intersection(memberline):
                IntroducedBy = MemberOfLine.intersection(memberline)
                print 'hello'
                PRID = content['PRID'].encode('utf-8').strip()
                print PRID
                PRTitle = content['PRTitle'].encode('utf-8').strip()
                PRReportedDate = str(content['PRReportedDate'])
                PRClosedDate = content['PRClosedDate'].encode('utf-8').strip()
                PRRelease = content['PRRelease'].encode('utf-8').strip()
                PRAttached = content['PRAttached'].encode('utf-8').strip()
                IntroducedBy = IntroducedBy
                # JiraRcaBeReqested = 'Yes'
                # LteCategory = 'TDD'

                if content['PRGroupIC'] == 'NIOYSR2' or content['PRGroupIC'] == 'LTE_DEVHZ1_CHZ_SPEC_UP':
                    TeamAssessor = 'jun-julian.hu@nokia-sbell.com'
                    insert_item('wangli', PRID, PRTitle, PRReportedDate, PRClosedDate, PRRelease, PRAttached,
                                IntroducedBy, TeamAssessor, jira)
                else:
                    TeamAssessor = addr_dict[linename]['fc']
                    insert_item(linename, PRID, PRTitle, PRReportedDate, PRClosedDate, PRRelease, PRAttached,
                                IntroducedBy, \
                                TeamAssessor, jira)


def update_from_tbox_tdd(jira):
    member_map = {}
    contents = reConnectProntoDbTdd()
    for content in contents:
        PRID = content['PRID'].encode('utf-8').strip()
        todo_item = Todo.query.get(PRID)
        # If already in WebApp table, then no need update anymore, keep the manual change valid.
        if todo_item:
            continue
        status, assignee, RcaSubtaskJiraId = JiraRequest(jira, PRID)
        # TDD only check Customer PR,Status==False means, this is not a PR from JIRA Customer
        if status is False:
            continue
        else:
            JiraIssueStatus = status
            JiraIssueAssignee = assignee
            RcaSubtaskJiraId = RcaSubtaskJiraId
            # JiraIssueStatus = GetJiraIssueStatus(issue)
        for linename in teams:
            email_name = addr_dict[linename]['email']
            with UseDatabaseDict(app.config['dbconfig']) as cursor:
                _SQL = "select * from user_info where lmEmail= '" + email_name + "'"
                cursor.execute(_SQL)
                members = cursor.fetchall()
            memberlist = []
            # members = TodoMember.query.filter_by(lineManager=linename).all()
            for member in members:
                displayname = member['displayName']
                email = displayname.encode('utf-8').strip()
                memberlist.append(email)
            member_map.setdefault(linename, memberlist)
            print 'before hello'
            resp = content['RespPerson'].encode('utf-8').strip()
            RespPerson = resp_members(resp)
            a = list(set(member_map[linename]).intersection(set(RespPerson)))
            memberline = set(RespPerson)
            retA = [val for val in RespPerson if val in member_map[linename]]
            MemberOfLine = set(member_map[linename])
            s = MemberOfLine.intersection(memberline)
            if MemberOfLine.intersection(memberline):
                IntroducedBy = MemberOfLine.intersection(memberline)
                print 'hello'
                PRID = content['PRID'].encode('utf-8').strip()
                print PRID
                PRTitle = content['PRTitle'].encode('utf-8').strip()
                PRReportedDate = str(content['PRReportedDate'])
                PRClosedDate = content['PRClosedDate'].encode('utf-8').strip()
                PRRelease = content['PRRelease'].encode('utf-8').strip()
                PRAttached = content['PRAttached'].encode('utf-8').strip()
                IntroducedBy = IntroducedBy
                JiraRcaBeReqested = 'Yes'
                LteCategory = 'TDD'

                if content['PRGroupIC'] == 'NIHZYSUP':
                    TeamAssessor = 'yuan_xing.wu@nokia-sbell.com'
                    insert_item_jira('wangli', PRID, PRTitle, PRReportedDate, PRClosedDate, PRRelease, PRAttached,
                                     IntroducedBy, LteCategory, JiraRcaBeReqested, TeamAssessor, JiraIssueStatus,
                                     JiraIssueAssignee, \
                                     RcaSubtaskJiraId)
                else:
                    TeamAssessor = addr_dict[linename]['fc']
                    insert_item_jira(linename, PRID, PRTitle, PRReportedDate, PRClosedDate, PRRelease, PRAttached,
                                     IntroducedBy, \
                                     LteCategory, JiraRcaBeReqested, TeamAssessor, JiraIssueStatus, JiraIssueAssignee, \
                                     RcaSubtaskJiraId)


def insert_item_common(team, PRID, PRTitle, PRReportedDate, PRClosedDate, PRRelease, PRAttached, IntroducedBy, \
                       LteCategory, JiraRcaBeReqested, TeamAssessor, JiraIssueStatus, JiraIssueAssignee,
                       RcaSubtaskJiraId):
    PROpenDays = daysBetweenDate(PRReportedDate, PRClosedDate)
    PRRcaCompleteDate = ''
    if daysBetweenDate(PRReportedDate, PRClosedDate) > 14:
        IsLongCycleTime = 'Yes'
    else:
        IsLongCycleTime = 'No'

    IsCatM = ''
    IsRcaCompleted = 'No'
    LongCycleTimeRcaIsCompleted = 'No'
    NoNeedDoRCAReason = ''
    RootCauseCategory = ''
    FunctionArea = ''

    CodeDeficiencyDescription = ''
    CorrectionDescription = ''
    RootCause = ''
    LongCycleTimeRootCause = ''

    IntroducedBy = IntroducedBy
    Handler = team

    LteCategory = LteCategory
    CustomerOrInternal = 'Yes'
    JiraFunctionArea = ''
    TriggerScenarioCategory = ''
    FirstFaultEcapePhase = ''
    FaultIntroducedRelease = ''
    TechnicalRootCause = ''
    TeamAssessor = TeamAssessor
    EdaCause = ''
    RcaRootCause5WhyAnalysis = ''
    JiraRcaBeReqested = JiraRcaBeReqested
    JiraIssueStatus = JiraIssueStatus
    JiraIssueAssignee = JiraIssueAssignee
    JiraRcaPreparedQualityRating = 10
    JiraRcaDeliveryOnTimeRating = 10
    RcaSubtaskJiraId = RcaSubtaskJiraId

    with UseDatabaseDict(app.config['dbconfig']) as cursor:
        _SQL = "select * from user_info where displayName = '" + JiraIssueAssignee + "'"
        cursor.execute(_SQL)
        items = cursor.fetchall()
    if len(items) != 0:
        emailname = items[0]['email'].encode('utf-8')
        lmEmail = items[0]['lmEmail'].encode('utf-8')
        if lmEmail in addr_dict1.keys():
            team = addr_dict1[lmEmail]
            TeamAssessor = emailname
            Handler = team
    # hello = User.query.filter_by(username=Handler).first()
    registered_user = Todo.query.filter_by(PRID=PRID).all()
    if len(registered_user) == 0:

        todo = Todo(PRID, PRTitle, PRReportedDate, PRClosedDate, PROpenDays, PRRcaCompleteDate, PRRelease, PRAttached,
                    IsLongCycleTime, \
                    IsCatM, IsRcaCompleted, NoNeedDoRCAReason, RootCauseCategory, FunctionArea,
                    CodeDeficiencyDescription, \
                    CorrectionDescription, RootCause, IntroducedBy, Handler, LteCategory, CustomerOrInternal,
                    JiraFunctionArea, TriggerScenarioCategory, \
                    FirstFaultEcapePhase, FaultIntroducedRelease, TechnicalRootCause, TeamAssessor, EdaCause,
                    RcaRootCause5WhyAnalysis, \
                    JiraRcaBeReqested, JiraIssueStatus, JiraIssueAssignee, JiraRcaPreparedQualityRating,
                    JiraRcaDeliveryOnTimeRating, \
                    RcaSubtaskJiraId)
        # g.user=Todo.query.get(team)
        # todo.user = g.user
        # print("todo.user = g.user=%s"%todo.user)
        hello = User.query.filter_by(username=Handler).first()
        todo.user_id = hello.id
        print("todo.user_id=hello.user_id=%s" % hello.id)
        db.session.add(todo)
        db.session.commit()
    else:
        todo_item = Todo.query.get(PRID)
        todo_item.IntroducedBy = IntroducedBy
        todo_item.Handler = Handler
        todo_item.LteCategory = LteCategory
        todo_item.CustomerOrInternal = CustomerOrInternal
        todo_item.JiraRcaBeReqested = JiraRcaBeReqested
        todo_item.JiraIssueStatus = JiraIssueStatus
        todo_item.TeamAssessor = TeamAssessor
        todo_item.JiraIssueAssignee = JiraIssueAssignee

        count = TodoJiraRcaPreparedQualityRating.query.filter_by(PRID=PRID).count()
        values = TodoJiraRcaPreparedQualityRating.query.filter_by(PRID=PRID).all()
        sum = 0

        if count != 0:
            for item in values:
                sum = sum + item.RatingValue
            todo_item.JiraRcaPreparedQualityRating = sum / count
        else:
            todo_item.JiraRcaPreparedQualityRating = 10

        current_time = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        dayspast = daysBetweenDate(PRClosedDate, current_time)

        with UseDatabaseDict(app.config['dbconfig']) as cursor:
            _SQL = "select * from user_info where displayName = '" + JiraIssueAssignee + "'"
            cursor.execute(_SQL)
            items = cursor.fetchall()
        if len(items) != 0:
            if JiraIssueStatus in ['Open', 'Reopened', 'In Progress'] and JiraRcaBeReqested == 'Yes':
                if dayspast <= 14:
                    todo_item.JiraRcaDeliveryOnTimeRating = 10
                else:
                    todo_item.JiraRcaDeliveryOnTimeRating = 24 - dayspast
            elif JiraIssueStatus in ['Closed', 'Resolved']:
                todo_item.IsRcaCompleted = 'Yes'
        """
            emailname = items[0]['email'].encode('utf-8')
            lmEmail = items[0]['lmEmail'].encode('utf-8')
            if lmEmail in addr_dict1.keys():
                team = addr_dict1[lmEmail]
                todo_item.TeamAssessor = emailname
                todo_item.Handler = team
        hello = User.query.filter_by(username=team).first()
        todo_item.user_id = hello.id
        """
        db.session.commit()
        print ("registered_user.PRTitle=%s" % PRID)

    registered_user = TodoLongCycleTimeRCA.query.filter_by(PRID=PRID).all()
    if len(registered_user) == 0 and IsLongCycleTime == 'Yes':
        print 'OK#################################################'
        todo = TodoLongCycleTimeRCA(PRID, PRTitle, PRReportedDate, PRClosedDate, PROpenDays, PRRcaCompleteDate,
                                    IsLongCycleTime, \
                                    IsCatM, LongCycleTimeRcaIsCompleted, LongCycleTimeRootCause, NoNeedDoRCAReason,
                                    Handler)

        hello = User.query.filter_by(username=team).first()
        todo.user_id = hello.id
        print("todo.user_id=hello.user_id=%s" % hello.id)
        db.session.add(todo)
        db.session.commit()
    elif IsLongCycleTime == 'Yes':
        todo_item = TodoLongCycleTimeRCA.query.get(PRID)
        todo_item.Handler = Handler
        hello = User.query.filter_by(username=team).first()
        todo_item.user_id = hello.id
        db.session.commit()
        print ("registered_user.PRTitle=%s" % PRID)


def check_assign_issue(jira):
    # issues = jira.search_issues('assignee=qmxh38')
    issues = jira.search_issues('project = MNRCA and assignee = qmxh38 and type = "Analysis subtask" and \
                                status not in (Resolved, Closed)')
    if len(issues):
        for issue in issues:
            summary = issue.fields.summary
            PRID = summary.split(' ', 2)[2]
            # PRID = "PR307541"
            # day1 = int(start.split('-', 2)[2])
            todo_item = Todo.query.get(PRID)
            if todo_item:  # PR in the rca table,just do the assignment and update assignee.
                TeamAssessor = todo_item.TeamAssessor
                with UseDatabaseDict(app.config['dbconfig']) as cursor:
                    _SQL = "select * from user_info where email = '" + TeamAssessor + "'"
                    cursor.execute(_SQL)
                    items = cursor.fetchall()
                if len(items) != 0:
                    emailname = items[0]['accountId'].encode('utf-8')
                    jira.assign_issue(issue, emailname)
                    todo_item.JiraIssueAssignee = items[0]['displayName'].encode('utf-8')
                    # issue.update(assignee={'name': emailname})
                    todo_item.JiraRcaBeReqested = 'Yes'
                    todo_item.RcaSubtaskJiraId = issue.key
                    todo_item.JiraIssueStatus = issue.fields.status
                # jira_assign()
                db.session.commit()
            else:  # PR not in the RCA table, first add it to RCA table and do the assignment.
                with UseDatabaseDict(app.config['dbconfig']) as cursor:
                    _conn_status = False
                    # PRID ='PR326676'
                    # _SQL = "select * from t_boxi_closed_pronto_daily where PRID='"+PRID+"'"
                    _SQL = "SELECT DISTINCT prcls.PRID,prcls.PRTitle, prcls.Platform,prcls.PRGroupIC, prcls.PRRelease, prcls.PRReportedDate,\
                     prcls.PRState, date_format(prcls.ClosedEnter, '%Y-%m-%d') as PRClosedDate,prcls.PRAttached,\
                    prnew.RespPerson FROM t_boxi_closed_pronto_daily as prcls LEFT JOIN t_boxi_new_pronto_daily as prnew\
                    ON prcls.PRID = prnew.PRID WHERE prcls.PRID='" + PRID + "'"
                    # _SQL = "select * from user_info where email = '" + JiraIssueAssignee + "'"
                    cursor.execute(_SQL)
                    contents = cursor.fetchall()
                # if len(contents):
                member_map = {}
                for content in contents:
                    PRID = content['PRID'].encode('utf-8').strip()
                    for linename in teams:
                        email_name = addr_dict[linename]['email']
                        with UseDatabaseDict(app.config['dbconfig']) as cursor:
                            _SQL = "select * from user_info where lmEmail= '" + email_name + "'"
                            cursor.execute(_SQL)
                            members = cursor.fetchall()
                        memberlist = []
                        # members = TodoMember.query.filter_by(lineManager=linename).all()
                        for member in members:
                            displayname = member['displayName']
                            email = displayname.encode('utf-8').strip()
                            memberlist.append(email)
                        member_map.setdefault(linename, memberlist)
                        print 'before hello'
                        resp = content['RespPerson'].encode('utf-8').strip()
                        RespPerson = resp_members(resp)
                        a = list(set(member_map[linename]).intersection(set(RespPerson)))
                        memberline = set(RespPerson)
                        retA = [val for val in RespPerson if val in member_map[linename]]
                        MemberOfLine = set(member_map[linename])
                        s = MemberOfLine.intersection(memberline)
                        if MemberOfLine.intersection(memberline):
                            IntroducedBy = MemberOfLine.intersection(memberline)
                            print 'hello'
                            PRID = content['PRID'].encode('utf-8').strip()
                            print PRID
                            PRTitle = content['PRTitle'].encode('utf-8').strip()
                            PRReportedDate = str(content['PRReportedDate'])
                            PRClosedDate = content['PRClosedDate'].encode('utf-8').strip()
                            PRRelease = content['PRRelease'].encode('utf-8').strip()
                            PRAttached = content['PRAttached'].encode('utf-8').strip()
                            IntroducedBy = IntroducedBy
                            LteCategory = content['Platform']
                            if LteCategory == 'TDLTE':
                                LteCategory = 'TDD'
                            if LteCategory == 'FDDMACPS':
                                LteCategory = 'FDD'
                            JiraRcaBeReqested = 'Yes'
                            JiraIssueStatus = issue.fields.status
                            RcaSubtaskJiraId = issue.key
                            # LteCategory = 'TDD'
                            if content['PRGroupIC'] == 'NIOYSR2' or content['PRGroupIC'] == 'LTE_DEVHZ1_CHZ_SPEC_UP':
                                TeamAssessor = 'jun-julian.hu@nokia-sbell.com'
                                # JiraIssueAssignee = TeamAssessor
                                team = 'wangli'
                            elif content['PRGroupIC'] == 'NIHZYSUP':
                                TeamAssessor = 'yuan_xing.wu@nokia-sbell.com'
                                # JiraIssueAssignee = TeamAssessor
                                team = 'wangli'
                                """
                                with UseDatabaseDict(app.config['dbconfig']) as cursor:
                                    _SQL = "select * from user_info where email = '" + JiraIssueAssignee + "'"
                                    cursor.execute(_SQL)
                                    items = cursor.fetchall()
                                if len(items) != 0:
                                    emailname = items[0]['accountId'].encode('utf-8')
                                    JiraIssueAssignee = items[0]['displayName'].encode('utf-8')
                                    jira.assign_issue(issue, emailname)
                                    issue.update(assignee={'name': emailname})
                                insert_item_common('wangli',PRID,PRTitle,PRReportedDate,PRClosedDate,PRRelease,PRAttached,IntroducedBy,\
                                                    LteCategory,JiraRcaBeReqested,TeamAssessor,JiraIssueStatus,JiraIssueAssignee,RcaSubtaskJiraId)
                                """
                            else:
                                TeamAssessor = addr_dict[linename]['fc']
                                # JiraIssueAssignee = TeamAssessor
                                team = linename

                            with UseDatabaseDict(app.config['dbconfig']) as cursor:
                                _SQL = "select * from user_info where email = '" + TeamAssessor + "'"
                                cursor.execute(_SQL)
                                items = cursor.fetchall()
                            if len(items) != 0:
                                # emailname='qmxh38'
                                emailname = items[0]['accountId'].encode('utf-8')
                                JiraIssueAssignee = items[0]['displayName'].encode('utf-8')
                                jira.assign_issue(issue, emailname)
                                # issue.update(assignee={'name': emailname})
                                todo_item.JiraRcaBeReqested = 'Yes'
                                todo_item.RcaSubtaskJiraId = issue.key
                                todo_item.JiraIssueStatus = issue.fields.status
                            insert_item_common(team, PRID, PRTitle, PRReportedDate, PRClosedDate, PRRelease,
                                               PRAttached, IntroducedBy, LteCategory, JiraRcaBeReqested, TeamAssessor, \
                                               JiraIssueStatus, JiraIssueAssignee, RcaSubtaskJiraId)


def quality_rating(jira):
    # todos = Todo.query.filter(Todo.JiraRcaBeReqested == 'Yes', ~Todo.JiraIssueStatus.in_(['Closed', 'Resolved'])).order_by(Todo.PRClosedDate.asc()).all()
    todos = Todo.query.filter(Todo.JiraRcaBeReqested == 'Yes',
                              Todo.JiraIssueStatus.in_(['Open', 'Closed', 'Resolved', 'In Progress', 'Reopened'])).all()
    # todos = Todo.query.filter( ~Todo.JiraIssueStatus.in_(['Closed', 'Resolved'])).order_by(Todo.PRClosedDate.asc()).all()
    for todo in todos:
        PRID = todo.PRID
        todo_item = Todo.query.get(PRID)
        JiraIssueStatus = todo_item.JiraIssueStatus
        JiraIssueId = todo_item.RcaSubtaskJiraId
        if JiraIssueId:
            issue = jira.issue(JiraIssueId)
            JiraIssueStatus = issue.fields.status
            JiraIssueAssignee = str(issue.fields.assignee)
        status, assignee, jiraissuekey = JiraRequest(jira, PRID)
        if status is False:
            continue
        else:
            JiraIssueStatus = status
            JiraIssueAssignee = assignee
            JiraIssueId = jiraissuekey
        todo_item.JiraIssueStatus = JiraIssueStatus
        todo_item.JiraIssueAssignee = JiraIssueAssignee
        todo_item.JiraRcaBeReqested = 'Yes'
        todo_item.RcaSubtaskJiraId = JiraIssueId
        PRClosedDate = todo_item.PRClosedDate
        # JiraIssueAssignee = todo_item.JiraIssueAssignee

        count = TodoJiraRcaPreparedQualityRating.query.filter_by(PRID=PRID).count()
        values = TodoJiraRcaPreparedQualityRating.query.filter_by(PRID=PRID).all()
        sum = 0
        if count != 0:
            for item in values:
                sum = sum + item.RatingValue
            todo_item.JiraRcaPreparedQualityRating = sum / count
        else:
            todo_item.JiraRcaPreparedQualityRating = 10

        current_time = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        dayspast = daysBetweenDate(PRClosedDate, current_time)
        with UseDatabaseDict(app.config['dbconfig']) as cursor:
            _SQL = "select * from user_info where displayName = '" + JiraIssueAssignee + "'"
            cursor.execute(_SQL)
            items = cursor.fetchall()
            if len(items) != 0:
                if JiraIssueStatus in ['Open', 'Reopened', 'In Progress']:
                    todo_item.IsRcaCompleted = 'No'
                    if dayspast <= 14:
                        todo_item.JiraRcaDeliveryOnTimeRating = 10
                    else:
                        todo_item.JiraRcaDeliveryOnTimeRating = 24 - dayspast
                elif JiraIssueStatus in ['Closed', 'Resolved']:
                    todo_item.IsRcaCompleted = 'Yes'
        db.session.commit()


def view_the_pr():
    """Display the contents of the log file as a HTML table."""
    with UseDatabaseDict(app.config['dbconfig']) as cursor:
        _SQL = "select * from t_boxi_closed_pronto_daily where PRGroupIC='LTE_DEVCAHZ_CHZ_UPMACPS'"
        _SQL = "SELECT DISTINCT prcls.PRID,prcls.PRTitle, prcls.PRGroupIC, prcls.PRRelease, prcls.PRReportedDate, prcls.PRState, \
                date_format(prcls.ClosedEnter, '%Y-%m-%d') as PRClosedDate,prcls.PRAttached,\
                prnew.RespPerson FROM t_boxi_closed_pronto_daily as prcls LEFT JOIN t_boxi_new_pronto_daily as prnew\
                ON prcls.PRID = prnew.PRID WHERE prcls.PRGroupIC in ('LTE_DEVCAHZ_CHZ_UPMACPS','LTE_DEVPFHZ_CHZ_UPMACPS')\
                 and prcls.PRState='Closed'and prcls.ClosedEnter >='2018-01-01'"
        cursor.execute(_SQL)
        contents = cursor.fetchall()
        count = len(contents)
        print count


def resp_members(b):
    members = []
    # b = 'Ma, Cong 2. (NSB - CN/Hangzhou),Ma, Cong 3. (NSB - CN/Hangzhou),'
    a = b.split('),')
    # c=a[0]+')'
    n = len(a)
    if n > 1:
        for i in range(n - 1):
            c = a[i] + ')'
            members.append(c.encode('utf-8').strip())
        members.append(a[n - 1].encode('utf-8').strip())
    else:
        members.append(b.encode('utf-8').strip())
    return members
    print a


def sleeptime(day, hour, min, sec):
    return day * 24 * 3600 + hour * 3600 + min * 60 + sec


counting = 0


def update():
    global counting
    s1 = '09:00'
    s2 = datetime.now().strftime('%H:%M')
    if s2 == s2:
        counting = counting + 1
        print 'Action now!'
        print counting
        jira = getjira()
        update_from_tbox_fdd(jira)
        update_from_tbox_tdd(jira)
        check_assign_issue(jira)
        quality_rating(jira)

        print 'update completed!!'
        second = sleeptime(0, 0, 1, 10)
        time.sleep(second)

        CAS - 120133 - Q1T3


def JIRAtest(jira):
    JiraRequest(jira, 'CAS-120133-Q1T3')



internal_task_dict={}
internal_task_dict['chenlong']={}
internal_task_dict['zhangyijie']={}
internal_task_dict['lanshenghai']={}
internal_task_dict['lizhongyuan']={}
internal_task_dict['xiezhen']={}
internal_task_dict['caizhichao']={}
internal_task_dict['yangjinyong']={}
internal_task_dict['liumingjing']={}
internal_task_dict['zhaoli']={}
internal_task_dict['zhuofei.chen@nokia-sbell.com']={}
internal_task_dict['maciej.1.sikorski@nokia.com']={}


task_status_dict={}
task_status_dict['chenlong']=[]
task_status_dict['zhangyijie']=[]
task_status_dict['lanshenghai']=[]
task_status_dict['lizhongyuan']=[]
task_status_dict['xiezhen']=[]
task_status_dict['caizhichao']=[]
task_status_dict['yangjinyong']=[]
task_status_dict['liumingjing']=[]
task_status_dict['zhaoli']=[]
task_status_dict['zhuofei.chen@nokia-sbell.com']=[]
task_status_dict['maciej.1.sikorski@nokia.com']=[]



internal_task_dict1={}
internal_task_dict1['chenlong']={}
internal_task_dict1['zhangyijie']={}
internal_task_dict1['lanshenghai']={}
internal_task_dict1['lizhongyuan']={}
internal_task_dict1['xiezhen']={}
internal_task_dict1['caizhichao']={}
internal_task_dict1['yangjinyong']={}
internal_task_dict1['liumingjing']={}
internal_task_dict1['zhaoli']={}
internal_task_dict1['zhuofei.chen@nokia-sbell.com']={}
internal_task_dict1['maciej.1.sikorski@nokia.com']={}


task_status_dict1={}
task_status_dict1['chenlong']=[]
task_status_dict1['zhangyijie']=[]
task_status_dict1['lanshenghai']=[]
task_status_dict1['lizhongyuan']=[]
task_status_dict1['xiezhen']=[]
task_status_dict1['caizhichao']=[]
task_status_dict1['yangjinyong']=[]
task_status_dict1['liumingjing']=[]
task_status_dict1['zhaoli']=[]
task_status_dict1['zhuofei.chen@nokia-sbell.com']=[]
task_status_dict1['maciej.1.sikorski@nokia.com']=[]


# JIRA New Arrival RCA/EDA detecting
internal_task_dict2={}
internal_task_dict2['chenlong']={}
internal_task_dict2['zhangyijie']={}
internal_task_dict2['lanshenghai']={}
internal_task_dict2['lizhongyuan']={}
internal_task_dict2['xiezhen']={}
internal_task_dict2['caizhichao']={}
internal_task_dict2['yangjinyong']={}
internal_task_dict2['liumingjing']={}
internal_task_dict2['zhaoli']={}
internal_task_dict2['zhuofei.chen@nokia-sbell.com']={}
internal_task_dict2['maciej.1.sikorski@nokia.com']={}


task_status_dict2={}
task_status_dict2['chenlong']=[]
task_status_dict2['zhangyijie']=[]
task_status_dict2['lanshenghai']=[]
task_status_dict2['lizhongyuan']=[]
task_status_dict2['xiezhen']=[]
task_status_dict2['caizhichao']=[]
task_status_dict2['yangjinyong']=[]
task_status_dict2['liumingjing']=[]
task_status_dict2['zhaoli']=[]
task_status_dict2['zhuofei.chen@nokia-sbell.com']=[]
task_status_dict2['maciej.1.sikorski@nokia.com']=[]



def get_device_by_ua(ua_string):
    # ua_string request.headers['User-Agent']
    # from ua_parser import user_agent_parser
    ua_dict = user_agent_parser.Parse(ua_string)
    user_agent_dict = ua_dict['user_agent']
    teminal_type = ua_dict['device']['family']
    if teminal_type.upper() == 'OTHER':
        teminal_type = 'PC'
    user_agent_version = (user_agent_dict['family'] + '/' +
                          user_agent_dict['major'] + '.' +
                          user_agent_dict['minor'] + '.' +
                          '0')
    return dict(zip(('TERMINAL_TYPE', 'OS_TYPE', 'LOGIN_DEV_SOFTWARE'),
                    (teminal_type, ua_dict['os']['family'],
                     user_agent_version)))


def get_remote_machine_info():
    remote_host = request.remote_addr
    try:
        print "IP address of %s: %s" % (remote_host, socket.gethostbyname(remote_host))

    except socket.error, err_msg:
        print "%s: %s" % (remote_host, err_msg)
    return remote_host

def get_login_info():
    remote_ip= get_remote_machine_info()
    user_dict=get_device_by_ua(request.headers['user-agent'])
    device=user_dict['TERMINAL_TYPE']
    browser=user_dict['LOGIN_DEV_SOFTWARE']
    os=user_dict['OS_TYPE']
    log_dict={}
    location='NOKIA'
    log_dict['IP']= remote_ip
    log_dict['BR']= browser
    log_dict['DEV']= device
    log_dict['OS']= os
    log_dict['LOC']=location
    return log_dict