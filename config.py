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
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost:3306/fddrca?charset=utf8'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://lmx:12345678@localhost:3306/blog?charset=utf8'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = 'secret_key'
app.config['DEBUG'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

JIRA_STATUS = {'Closed': 2, 'Reopened' : 3, 'In Progress' : 4, 'Resolved' : 5}
AnalysisIssueCaseType = {'RCA':u'219575','EDA':u'219576','RCA and EDA':'219892'}
ChildIssueType = {'Analysis subtask':u'19800','Action for RCA':u'19804','Action for EDA':u'19806'}

TriggeringCategory = {  'Installation & Startup': u'219294',
                        'SW Upgrade':u'219295',
                        'SW Fallback':u'219296',
                        'Process of Configuration / Reconfiguration':u'219297',
                        'Not Supported Configuration':u'219298',
                        'OAM Operations':u'219299',
                        'Feature Interaction & interoperability':u'219300',
                        'OAM Robustness (high Load / stressful scenarios/long duration)':u'219301',
                        'Telecom Robustness (high Load / mobility /stressful scenarios/long duration)':u'219302',
                        'Debug (Counters/Alarms/Trace/Resource monitoring)':u'219303',
                        'Reset & Recovery':u'219304',
                        'HW Failure':u'219305',
                        'Required customer/vendor specific equipment':u'219306',
                        'Unknown triggering scenario':u'219307'
                        }

FaultShouldHaveBeenFound = {'Unit / System Component Test (UT/SCT)':{'id':u'219533'},
                            'Entity Test - Regression':{'id':u'219534'},
                            'Entity Test - New Feature':{'id':u'219535'},
                            'System Test - Regression':{'id':u'219536'},
                            'System Test - New Feature':{'id':u'219537'},
                            'Interoperability Testing':{'id':u'219538'},
                            'Performance Testing':{'id':u'219539'},
                            'Stability Testing':{'id':u'219540'},
                            'Negative/Adversarial Testing':{'id':u'219541'},
                            'Network Level Testing':{'id':u'219542'},
                            'First Office Application':{'id':u'219543'}}

# RcaCauseType = {'None':								        {'id':u'-1'},
#                 'Standards':								{'id':u'192644'},
#                 'HW Problem':                               {'id':u'192645'},
#                 '3rd Party Products':                       {'id':u'192646'},
#                 'Missing Requirement':                      {'id':u'192647'},
#                 'Incorrect Requirements':                   {'id':u'192648'},
#                 'Unclear Requirements':                     {'id':u'192649'},
#                 'Changing Requirements':                    {'id':u'192650'},
#                 'Feature Interaction':                      {'id':u'192651'},
#                 'Design Deficiency':                        {'id':u'192652'},
#                 'Lack of Design Detail':                    {'id':u'192653'},
#                 'Defective Fix':                            {'id':u'192654'},
#                 'Feature  Enhancement':                     {'id':u'192655'},
#                 'Code Standards':                           {'id':u'192656'},
#                 'Configuration Mgmt - Merge':               {'id':u'192658'},
#                 'Documentation Issue':                      {'id':u'192659'},
#                 'Dependencies from Other Documentation':    {'id':u'192660'},
#                 'Code Error':                               {'id':u'192661'},
#                 'Code Complexity':                          {'id':u'192662'}
#                 }
#
# EdaCauseType = {
#                 'None':								                       {'id':u'-1'},
#                 'Traceability to Requirements':							   {'id':u'193960'},
#                 'incorrect Testcase':                                      {'id':u'193961'},
#                 'Scenario Not predicted - Customer Specific Test Scope':   {'id':u'193962'},
#                 'Module/Unit tests - Test Scope':                          {'id':u'193963'},
#                 'Entity/Feature Tests - Test Scope':                       {'id':u'193964'},
#                 'Regression Tests -Test Scope':                            {'id':u'193965'},
#                 'Network Verification  -- Test Scope':                     {'id':u'193966'},
#                 'Solution Verification - Test Scope':                      {'id':u'193967'},
#                 'Performance - Test Scope':                                {'id':u'193968'},
#                 'Non-Functianl  - Test Scope':                             {'id':u'193969'},
#                 'Maintenance Test Scope':                                  {'id':u'193970'},
#                 'E2E  Verification -- Test Scope':                         {'id':u'193971'},
#                 'Test Plan':                                               {'id':u'193972'},
#                 'Test Strategy --  Content missing/not covered/Configuration not tested': {'id':u'193973'},
#                 'Missing Test case review':                                {'id':u'193974'},
#                 'Unknown/Unclear test configurations':                     {'id':u'193975'},
#                 'Unforeseen upgrade Paths':                                {'id':u'193976'},
#                 'Unclear Load Model':                                {'id':u'193977'},
#                 'Missing Compatibility Tests':                       {'id':u'193978'},
#                 'Code review missed':                                {'id':u'193979'},
#                 'Configuration missing/misunderstood/incomplete':              {'id':u'219275'},
#                 'Scenario missing/misunderstood/incomplete':                   {'id':u'219276'},
#                 'Extraordinary scenario - Very difficult to recreate defect':  {'id':u'219277'},
#                 'Customer documentation not reviewed/tested':                  {'id':u'219278'},
#                 'Functional Testcase missing/misunderstood/incomplete':        {'id':u'219279'},
#                 'Non-Functional Testcase missing/misunderstood/incomplete':    {'id':u'219280'},
#                 'Regression Testcase missing/misunderstood/incomplete':        {'id':u'219281'},
#                 'Robustness Testcase missing/misunderstood/incomplete':        {'id':u'219282'},
#                 'Test Blocked : Lack of Hardware/Test Tools':                  {'id':u'219283'},
#                 'Test Blocked : Needed SW not available':                      {'id':u'219284'},
#                 'Test run too early in the release':                           {'id':u'219285'},
#                 'Planned Test run post delivery':                              {'id':u'219286'},
#                 'Planned Test not run':                                {'id':u'219287'},
#                 'Out of Testing Scope':                                {'id':u'219288'},
#                 'insufficient testing of changes/fixes':                                {'id':u'219289'},
#                 'insufficient test duration/iterations':                                {'id':u'219290'},
#                 'Fix was available but was not delivered':                              {'id':u'219291'},
#                 'incorrect analysis of test result, marked passed when actually failed': {'id':u'219292'},
#                 'intermittent defect':                                  {'id':u'219293'}}

RcaCauseType ={
'None':                                     {'id':u''},
'Requirements':                             {'id':u'236010'},
'Architecture':                             {'id':u'236011'},
'High_Level_Design':                        {'id':u'236012'},
'Low_Level_Design':                         {'id':u'236013'},
'Code':                                     {'id':u'236014'},
'User_Documentation_including_Release_Note':{'id':u'236015'},
'Configuration_and_Fault_Management':       {'id':u'236016'},
'Collaborated_Mode_with_Suppliers':         {'id':u'236017'},
# 'None':                            {'id':u''},
# 'Requirements':                    {'id':u'236010'},
# 'Architecture ':                   {'id':u'236011'},
# 'HighLevelDesign':                 {'id':u'236012'},
# 'LowLevelDesign':                  {'id':u'236013'},
# 'Code':                            {'id':u'236014'},
# 'UserDocumentationAndReleaseNotes':{'id':u'236015'},
# 'ConfigurationAndFaultManagement': {'id':u'236016'},
# 'CollaborationWithSuppliers':      {'id':u'236017'},

}

ChildRootCauseCategory ={
'None':                               {'id':u''},
#Requirements:
'Changing Requirement':                                              {'id':u'236018'},
'Customer specific Configuration/traffic requirements not accounted for':{'id':u'236019'},
'Missing Requirement':                                               {'id':u'236020'},
'Incorrect Requirement':                                             {'id':u'236021'},
'Unclear Requirement':                                               {'id':u'236022'},
'Misunderstood Customer Requirement':                                {'id':u'236023'},
'Late added Feature(s)':                                             {'id':u'236024'},
'Standards Interpretation Error':                                    {'id':u'236025'},
#Architecture
# 'Interworking error -  feature or component interaction':{'id':u'236026'},
'Interworking error -  feature or component interaction.':{'id':u'236026'},
'Memory consumption error':                              {'id':u'236027'},
'CPU overload error':                                    {'id':u'236028'},
'Software robustness error':                             {'id':u'236029'},
'Stability error':                                       {'id':u'236030'},
'Architecture gap':                                      {'id':u'236031'},
'Arcitecture specification error':                       {'id':u'236032'},
#HighLeveDesign
'Hardware compatibility':                    {'id':u'236034'},
'3rd Party compatibility / interoperability':{'id':u'236035'},
'Legacy interaction error':                  {'id':u'236036'},
'High level design missing/gap':             {'id':u'236037'},
'Design error':                              {'id':u'236038'},
#LowLevelDesign
'Low level design missing/gap':                                                  {'id':u'236040'},
'Deficient design/ design Error':                                                 {'id':u'236041'},
'Design knowledge, skills, competence (timer management, buffer handling, etc.)':{'id':u'236042'},
# 'Design knowledge skills competence_Timer Management Buffer Handling etc_':{'id':u'236042'},
#Code
'Code too complex':                   {'id':u'236043'},
'Coding logic error':                 {'id':u'236044'},
'Code language knowledge/expertise':{'id':u'236045'},
'Coding standards violations':        {'id':u'236046'},
'Implementation missing':             {'id':u'236047'},
'Implementation error':               {'id':u'236048'},
#CuDo
'Incorrect information used to create End-User Documentation':              {'id':u'236049'},
'Missing content/ step in procedure':                                       {'id':u'236050'},
'Missing detailed content (delivered content not sufficient from user PoV)':{'id':u'236051'},
'Outdated content':                                                         {'id':u'236052'},
'Language error':                                                           {'id':u'236053'},
'Incorrect information in the change note':                                 {'id':u'236054'},
'Inconsistency within the same customer document':                          {'id':u'236055'},
'User documentation not tested':                                            {'id':u'236056'},
#ConfigAndFaultManagement
'Build error/ incorrect version':                    {'id':u'236057'},
'Merge error':                                       {'id':u'236058'},
'Missed defect inheritance or porting process error':{'id':u'236059'},
#CollaborationWithSuppliers
'Delivery failure':              {'id':u'236061'},
'Lack of specification':         {'id':u'236062'},
'Documentation failure':         {'id':u'236063'},
'Implementation failure':        {'id':u'236064'},
'Lack of testing':               {'id':u'236065'},
'Missing requirement':           {'id':u'236066'},
'Project management':            {'id':u'236067'},
'3rd party software limitations':{'id':u'236068'},
}

EdaCauseType ={
'None':                                         {'id':u''},
'Technical_Reviews':                            {'id':u'236248'},
'Code_Analysis_Tools':                          {'id':u'236241'},
'Unit_Tests':                                   {'id':u'236242'},
'System_Component_or_Module_Test':              {'id':u'236243'},
'Entity_or_Integration_and_Verification_Test':  {'id':u'236244'},
'System_Verification_Functional_Test':          {'id':u'236245'},
'System_verification_Non_Functional_Testing':   {'id':u'236246'},
'Collaborated_Mode_with_Suppliers':             {'id':u'236247'},
# 'None':                                  {'id':u''},
# 'TechnicalReviews':                      {'id':u'236248'},
# 'CodeAnalysisTools':                     {'id':u'236241'},
# 'UnitTest':                              {'id':u'236242'},
# 'SystemComponentModuleTest':             {'id':u'236243'},
# 'EntityIntegrationAndVerificationTest':  {'id':u'236244'},
# 'SystemVerificationFunctionalTest':      {'id':u'236245'},
# 'SystemVerificationNonFunctionalTesting':{'id':u'236246'},
# 'CollaborationWithSuppliers':            {'id':u'236247'},
}

ChildEscapeCauseCategory ={
'None':
{
'None':                                     {'id':u''}
},
'Technical_Reviews':
{
'Requirements not reviewed with customer':  {'id':u'236249'},
'Internal requirement review gap':          {'id':u'236250'},
'Architecture review gap':                  {'id':u'236251'},
'Design review gap':                        {'id':u'236252'},
'Missing analysis of impact of change':     {'id':u'236253'},
'Code review gap':                          {'id':u'236254'},
'Test strategy review gap':                 {'id':u'236255'},
'Unit or component testcase review gap':    {'id':u'236256'},
'Entity or integration test review gap':    {'id':u'236257'},
'System testcase review gap':               {'id':u'236258'},
'CuDo internal review gap':                 {'id':u'236259'}
},
#Static Tool
'Code_Analysis_Tools':
{
'Test tools availability/ capability':       {'id':u'236260'},
'Inappropriate tool usage':                  {'id':u'236261'},
'Insufficient use of static analyzers': {'id':u'236262'},
'Insufficient use of dynamic analyzers':{'id':u'236263'}
},
#UT
'Unit_Tests':
{
'Code not covered by test':                                      {'id':u'236264'},
'Wrong check in testcase':                                       {'id':u'236265'},
'Stubs or mocks do not reflect real world scenarios': {'id':u'236266'},
'Objects initialized with wrong values':                         {'id':u'236267'},
'Error cases/paths not tested':                                  {'id':u'236268'}
},
#SCT
'System_Component_or_Module_Test':
{
'Functionality not covered':                   {'id':u'236269'},
'Feature interaction coverage gap':            {'id':u'236270'},
'Configuration coverage gap':                  {'id':u'236271'},
'Limitation of test framework or environment': {'id':u'236272'},
'Corner case and error case test gap':         {'id':u'236273'},
'Test did not execute the planned scenario':   {'id':u'236274'}
},
#ET
# 'None':                                                                      {'id':u''},
'Entity_or_Integration_and_Verification_Test':
{
'Requirement coverage gap':                                                     {'id':u'236275'},
'Limitation of test framework or environment':                                 {'id':u'236276'},
'Configuration coverage gap':                                                   {'id':u'236277'},
'Test did not execute the planned scenario':                                    {'id':u'236278'},
'Exploratory testing (negative, sequence, abnormal, boundary, corner case) gap':{'id':u'236279'}
},
#ST
'System_Verification_Functional_Test':
{
'Network or solution verification testing gap':                                  {'id':u'236281'},
'Regression test gap':                                                           {'id':u'236282'},
'Configuration coverage gap':                                                    {'id':u'236283'},
'Feature interaction coverage gap':                                              {'id':u'236284'},
'Exploratory testing (negative, sequence, abnormal, boundary, corner case) gap': {'id':u'236285'},
'Testing of UE software':                                                        {'id':u'236286'},
'Insufficient Testing of 3rd Party SW/HW':                                       {'id':u'236287'},
'Limitation of test framework or environment':                                   {'id':u'236288'},
'Test automation gap':                                                      {'id':u'236289'},
'Test did not execute the planned scenario':                                     {'id':u'236290'},
'Requirement coverage gap':                                                      {'id':u'236510'},
'Not reproducible in Nokia lab - can be detected in live network':               {'id':u'236291'},
'Performance measurement verification gap':                                      {'id':u'236511'}
},
#STNonFunctional
'System_verification_Non_Functional_Testing':
{
'Performance testing gap':                      {'id':u'236292'},
'Robustness/stability test gap':                {'id':u'236293'},
'Limitation of test framework or environment':  {'id':u'236294'},
'Test automation gap':                          {'id':u'236295'},
'Testcase was not executed.':                   {'id':u'236296'}
},
#CollaborationWithSuppliers
'Collaborated_Mode_with_Suppliers':
{
'Delivery failure':              {'id':u'236297'},
'Lack of specification':         {'id':u'236298'},
'Documentation failure':         {'id':u'236299'},
'Implementation failure':        {'id':u'236300'},
'Lack of testing':               {'id':u'236301'},
'Missing requirement':           {'id':u'236302'},
'Project management':            {'id':u'236303'},
'3rd Party software limitations':{'id':u'236304'}
}
}

RcaActionType ={
'None':                                                   {'id':u'-1'},
'Requirements Improvement':                               {'id':u'236225'},
'Architecture Improvement':                               {'id':u'236226'},
'High-Level Design Improvement':                          {'id':u'236227'},
'Low-Level Design Improvement':                           {'id':u'236228'},
'Coding Quality Improvement':                             {'id':u'236229'},
'User Documentation (including Release Note) Improvement':{'id':u'236230'},
'Configuration and Fault Management Improvement':         {'id':u'236231'},
'Knowledge/ Expertise/ Training Improvement':               {'id':u'236232'},
}

EdaActionType={
'None':                                                     {'id':u'-1'},
'Technical Reviews Improvement':                            {'id':u'236233'},
'Code Analysis Tools Improvement':                          {'id':u'236234'},
'Unit Test Improvement':                                    {'id':u'236235'},
'System Component / Module Test Improvement':                 {'id':u'236236'},
'Entity/Integration and Verification Test Improvement':     {'id':u'236237'},
'System Verification Functional Test Improvement':          {'id':u'236238'},
'System Verification Non-Functional Testing Improvement':   {'id':u'236239'},
}
#JiraSubTask Case Type
JiraSubTaskCaseType = {'RCA':u'219575','EDA':u'219576','RCA and EDA':'219892'}
#Analysis subtask:19800,Action for RCA:19804,Action for EDA:19806
# JiraChildIssueType = {'Analysis subtask':u'19800','Action for RCA':u'19804','Action for EDA':u'19806'}

JiraChildIssueType ={'RCA':u'19804','EDA':u'19806'}




PriorityDict = {
    "1": 'Blocker',
    "2": 'Critical',
    "3": 'Major',
    "4": 'Minor',
    "5": 'Trivial',
    "6": 'Documentary',
    "10000": 'Unknown',
    "10001": 'Medium',
    "10002": 'Normal',
    "10100": 'High',
    "10101": 'Low',
}
SourceListDict = {
    "": 'None',
    "206960": 'NCDR',
    "206961": 'DQR deep dive.CES (VoC)',
    "206962": 'Internal R & D improvement',
    "206963": 'Lessons learned',
}
BusinessUnitDict = {
    "-1": 'None',
    "189744": 'Mobile Networks Products',
    "189745": 'Converged Core',
    "189746": 'Advanced Mobile Networks Solutions (AMS)',
    "189747": 'MN Service',
}

BusinessLineDict = {
    "-1": 'None',
    "205171": 'LTE',
    "205172": 'HetRAN',
    "205173": '5G',
    "205174": 'RF&AA',
    "205175": 'BBP',
    "205176": 'RMA',
    "205177": 'Customer Support',
    "205178": 'Architecture',
    "205179": 'Telco Cloud',
    "205180": '3G Core',
    "205181": 'Cloud SDM',
    "205182": 'Cloud IMS',
    "205183": 'Customer and Solution',
    "205184": 'Small Cell & WiFi Solutions',
    "205185": 'Public Sector, Complementary Solutions and Partner',
    "205187": 'X-Haul',
    "205188": 'NA',
    "205189": 'WVS',
    "219023": 'SRAN',
    "280313": 'Airphone',
    "276424": 'CDS',
    "280311": 'ECP',
    "280310": 'SoC',
    "280312": 'TRS',
    "320812": 'NM',
}

ProductLineDict = {
    "-1":'None',
    "179991":'AED',
    "179992":'BBP HW',
    "179993":'BBP OPSW',
    "179995":'BTS Site Manager',
    "179996":'CFX',
    "179997":'Cloud BTS',
    "179998":'CuDo',
    "179999":'DCM',
    "180000":'FDD LTE',
    "180001":'Femto',
    "180002":'Flexi Platform SW',
    "180003":'Flexi Zone',
    "180004":'GSM BTS',
    "180005":'HetRAN BTS',
    "180006":'HSS/vHSS',
    "180007":'HW',
    "180008":'MEC',
    "180009":'Metro',
    "180010":'MGW/OSP',
    "180011":'MSS',
    "180012":'N/A',
    "180013":'NCIO',
    "180014":'NDCS',
    "180015":'NLS',
    "180016":'NT-HLR/vHLR',
    "180017":'One NDS',
    "180018":'One-EIR ',
    "180019":'One-MNP',
    "180020":'oTAS',
    "180021":'PMOD - VGP',
    "180022":'RFHW',
    "180023":'RFSW',
    "180024":'RNC, BSC, RCP, vRNC',
    "180025":'SDL',
    "180026":'SoC',
    "180027":'SRAN/SBTS',
    "180028":'TD LTE',
    "180029":'WBTS',
    "180030":'WiFi/ZC',
    "180031":'GSM_BTS',
    "180032":'5G Application',
    "180033":'5G L1',
    "180034":'nTAS',
    "280316":'Airphone',
    "280314":'ECP',
    "280315":'TRS',
# <option value="310811">MN RAN NM SON</option>
    "310811":'MN RAN NM SON',
#<option value="321212">NOM</option>
    "321212":'NOM',
}


CustomerNameDict = {
    "-1": 'None',
    "206299": 'ADVANCED WIRELESS NETWORKS CO., LTD',
    "206300": 'AIS, Thailand',
    "206301": 'America Movil Head Office, Mexico, incl.AMX Colombia',
    "206302": 'AMX',
    "206303": 'AMX(Claro), Argentina',
    "206304": 'AMX(Claro), Chile',
    "206305": 'AT&T, USA',
    "206306": 'Avea',
    "206307": 'Bell Canada',
    "206308": 'BELL MOBILITY INC.',
    "206309": 'BHARTI',
    "206310": 'Bharti, India',
    "206311": 'BSNLMTNL',
    "206312": 'BT, EE & MBNL, UK',
    "206313": 'CA',
    "206314": 'CEWA',
    "206315": 'China Mobile, China',
    "206316": 'China Telecom, China',
    "206317": 'China Unicom, China',
    "206318": 'Chunghwa Telecom, Taiwan',
    "206319": 'DT Croatia',
    "206320": 'DT, Germany',
    "206321": 'Elisa',
    "206322": 'ERICSSON TELECOMUNICAZIONI S.P.A.WIND IT',
    "206323": 'EVERYTHING EVERYWHERE LIMITED(ORANGE PCS)',
    "206324": 'France Telecom',
    "206325": 'Free, France',
    "206326": 'HBTSCIF',
    "206327": 'HBTSSB',
    "206328": 'Hutchison 3G UK',
    "206329": 'Hutchison IRL',
    "206330": 'ICE Communication Norge AS',
    "206331": 'IDEA',
    "206332": 'IDEA CELLULAR LTD - KERELA',
    "206333": 'Idea, India',
    "206334": 'Indosat, Indonesia',
    "206335": 'IRANCELL',
    "206336": 'KDDI, Japan',
    "206337": 'Korea Telecom, Korea',
    "206338": 'KT CORPORATION',
    "206339": 'KT DJ Korea',
    "206340": 'KT Korea',
    "206341": 'LG U +, Korea',
    "206342": 'LOCOP',
    "206343": 'MBNL',
    "206344": 'Megafon, Russia',
    "206345": 'MOBILE TELECOMMUNICATIONS, SAUDI',
    "206346": 'MobileOne Ltd.',
    "206347": 'Mobily, Saudi Arabia',
    "206348": 'MTS, Russia',
    "206349": 'MUV',
    "206350": 'NA',
    "206351": 'NTT DoCoMo, Japan',
    "206352": 'O2 CZECH REPUBLIC',
    "206353": 'O2 GBR',
    "206354": 'O2, HU',
    "206355": 'OI',
    "206356": 'Oi, Brazil',
    "206357": 'Ooredoo Tunisie S.A.',
    "206358": 'Ooredoo, Myanmar',
    "206359": 'Ooredoo, Qatar',
    "206360": 'Optus, Australia',
    "206361": 'ORANGE',
    "206362": 'Orange, France',
    "206363": 'PLDT Smart, Philipines',
    "206364": 'PROXIMUS, BE',
    "206365": 'PT Telkomsel',
    "206366": 'Q-TEL',
    "206367": 'SAFARICOM',
    "206368": 'SAV',
    "206369": 'SFR, France',
    "206370": 'SK telecom, Inc',
    "206371": 'SK Telecom, Korea',
    "206372": 'SKIL',
    "206373": 'Softbank (incl. WCP, Y-Mobile), Japan',
    "206374": 'Sprint, USA',
    "206375": 'STC, SaudiArabia',
    "206376": 'T COM DEU',
    "206377": 'T-Mobile, Deutschland',
    "206378": 'T-Mobile Deutschland',
    "206379": 'T-MOBILE POLSKA S.A.',
    "206380": 'T-Mobile, USA',
    "206381": 'Taiwan Mobile, Taiwan',
    "206382": 'TATA',
    "206383": 'TELE2 NLD',
    "206384": 'Tele2, Russia',
    "206385": 'Telecom(TIM), Italia',
    "206386": 'TELECOM ITALIA S.P.A.(MOBILE)',
    "206387": 'Telefonica O2, UK',
    "206388": 'Telefonica, Germany',
    "206389": 'Telefonica, Spain',
    "206390": 'TELIA MOBILE AB, SE',
    "206391": 'Telkomsel, Indonesia',
    "206392": 'TF',
    "206393": 'THM',
    "206394": 'TIM',
    "206395": 'TIM, Brazil',
    "206397": 'UNITED STATES CELLULAR CORP.',
    "206398": 'US MA',
    "206399": 'VERIZON',
    "206400": 'Verizon, USA',
    "206401": 'VF',
    "206402": 'Viettel, Vietnam',
    "206403": 'Vimpelcom, Russia',
    "206404": 'Vodacom(Pty.) Ltd.',
    "206405": 'Vodacome, South Africa(RSA)',
    "206406": 'Vodafone - Chennai',
    "206407": 'VODAFONE EGYPT TEL',
    "206408": 'Vodafone, India',
    "206409": 'Vodafone, Italy',
    "206410": 'VTG AFR TZ(VNM)',
    "206411": 'WE',
    "206412": 'Wind, Canada',
    "206413": 'Zain Saudi Arabia',
    "206414": 'Vodafone',
    "206415": 'CUC',
    "206416": 'Bharti Airtel Limited',
    "206417": 'MTS UA',
    "206418": 'T-MOBILE USA',
    "206419": 'SFR Siege',
    "206420": 'Optus',
    "206421": 'SOFTBANK MOBILE Corp.',
    "206422": 'Telefonica Moviles de Espana',
    "206423": 'Vodafone UK Limited',
    "206424": 'SoftBank Corp.',
    "206425": 'Optus Networks Pty Ltd',
    "206426": 'ORANGE SKILL CENTER',
    "206427": 'Tt-Netvaerket P/S',
    "206428": 'IDEA CELLULAR LTD - UPEAST',
    "206429": 'Free Mobile',
    "213306": 'CMCC Zhejiang',
    "213307": 'CMCC Fujian',
    "213308": 'CMCC Hunan',
    "213309": 'CUC Shanghai',
}

CuDoBusinessLineDict = {
"-1": 'None',
"205152": 'LTE',
"205153": 'HetRAN',
"205154": '5G',
"205155": 'RF&AA',
"205156": 'BBP',
"205157": 'RMA',
"205158": 'Customer Support',
"205159": 'Architecture',
"205160": 'Telco Cloud ',
"205161": '3G Core',
"205162": 'Cloud SDM',
"205163": 'Cloud IMS ',
"205164": 'Customer and Solution',
"205165": 'Small Cell & WiFi Solutions',
"205166": 'IoT',
"205167": 'Public Sector, Complementary Solutions and Partner',
"205168": 'X-Haul',
"205169": 'NA',
}
CuDoProductLineDict ={
"-1": 'None',
"180035": 'FDD LTE',
"180036": 'TD LTE',
"180037": 'RNC, BSC, RCP, vRNC',
"180038": 'WBTS',
"180039": 'GSM BTS',
"180040": 'SRAN/SBTS',
"180041": 'N/A',
"180042": 'RFHW',
"180043": 'RFSW',
"180044": 'BBP HW',
"180045": 'BBP Site Manager',
"180046": 'BBP OPSW',
"180047": 'CuDo',
"180048": 'SoC',
"180049": 'MGW/OSP',
"180050": 'MSS',
"180051": 'Flexi Platform SW',
"180052": 'HW',
"180053": 'One NDS',
"180054": 'NT-HLR/vHLR',
"180055": 'HSS/vHSS',
"180056": 'CFX',
"180057": 'oTAS',
"180058": 'NLS',
"180059": 'PMOD - VGP',
"180060": 'Flexi Zone',
"180061": 'WiFi/ZC',
"180062": 'Femto',
"180063": 'Metro',
"180064": 'SDL',
"180065": 'NDCS',
"180066": 'DCM',
"180067": 'NCIO',
"180068": 'One-EIR',
"180069": 'One-MNP',

}

CuDoCustomerNameDict = {
"-1": 'None',
"206430": 'America Movil Head Office, Mexico, incl. AMX Colombia',
"206431": 'AMX',
"206432": 'AT&T Mobility',
"206433": 'AT&T, USA',
"206434": 'Bell Canada',
"206435": 'Bell Mobility Inc.',
"206436": 'BHARTI',
"206437": 'Bharti, India',
"206438": 'BSNLMTNL',
"206439": 'BT, EE & MBNL, UK',
"206440": 'CA',
"206441": 'CEWA',
"206442": 'China Mobile, China',
"206443": 'China Telecom, China',
"206444": 'China Unicom, China',
"206445": 'Chunghwa Telecom, Taiwan',
"206446": 'Claro Argentina',
"206447": 'CT Jiangsu',
"206448": 'DT, Germany',
"206449": 'Egyptian Company for Mobile Service',
"206450": 'Everything Everywhere Limited (Orange PCS)',
"206451": 'France Telecom',
"206452": 'IDEA',
"206453": 'Idea, India',
"206454": 'Indosat, Indonesia',
"206455": 'KDDI, Japan',
"206456": 'LG U+, Korea',
"206457": 'LOCOP',
"206458": 'Megafon, Russia',
"206459": 'Mobily, Saudi Arabia',
"206460": 'MTS, Russia',
"206461": 'MUV',
"206462": 'NA',
"206463": 'NTT DoCoMo, Japan',
"206464": 'OI',
"206465": 'Oi, Brazil',
"206466": 'Optus Networks Pty Ltd',
"206467": 'Optus, Australia',
"206468": 'ORANGE',
"206469": 'Orange, France',
"206470": 'SAV',
"206471": 'SFR, France',
"206472": 'SKIL',
"206473": 'Softbank (incl. WCP, Y-Mobile), Japan',
"206474": 'SoftBank Corp.',
"206475": 'Sprint, USA',
"206476": 'STC, Saudi Arabia',
"206477": 'T-Mobile Deutschland',
"206478": 'T-Mobile, USA',
"206479": 'Taiwan Mobile Co Ltd',
"206480": 'Taiwan Mobile, Taiwan',
"206481": 'Taiwan Star Telecom Co., Ltd',
"206482": 'TATA',
"206483": 'Telefonica, Germany',
"206484": 'Telefonica, Spain',
"206485": 'Telkomsel, Indonesia',
"206486": 'TF',
"206487": 'THM',
"206488": 'TIM',
"206489": 'TMO US',
"206490": 'US MA',
"206491": 'VERIZON',
"206492": 'Verizon, USA',
"206493": 'VF',
"206494": 'Vodafone - UP East',
"206495": 'Vodafone Omnitel N.V. (Vodafone Italy)',
"206496": 'Vodafone, India',
"206497": 'Vodafone, Italy',
"206498": 'WE',

}

# TriggeringCategory = {  'Installation & Startup': u'219294',
#                         'SW Upgrade':u'219295',
#                         'SW Fallback':u'219296',
#                         'Process of Configuration / Reconfigurationu':u'219297',
#                         'Not Supported Configuration':u'219298',
#                         'OAM Operations':u'219299',
#                         'Feature Interaction & interoperability':u'219300',
#                         'OAM Robustness (high Load / stressful scenarios/long duration)':u'219301',
#                         'Telecom Robustness (high Load / mobility /stressful scenarios/long duration)':u'219302',
#                         'Debug (Counters/Alarms/Trace/Resource monitoring)':u'219303',
#                         'Reset &amp; Recovery':u'219304',
#                         'HW Failure':u'219305',
#                         'Required customer/vendor specific equipment':u'219306',
#                         'Unknown triggering scenario':u'219307'
#                         }
#
# FaultShouldHaveBeenFound = {'Unit/System Component Test (UT/SCT)':{'id':u'219533'},
#                             'Entity Test - Regression':{'id':u'219534'},
#                             'Entity Test - New Feature':{'id':u'219535'},
#                             'System Test - Regression':{'id':u'219536'},
#                             'System Test - New Feature':{'id':u'219537'},
#                             'Interoperability Testing':{'id':u'219538'},
#                             'Performance Testing':{'id':u'219539'},
#                             'Stability Testing':{'id':u'219540'},
#                             'Negative/Adversarial Testing':{'id':u'219541'},
#                             'Network Level Testing':{'id':u'219542'},
#                             'First Office Application':{'id':u'219543'}}

# RcaCauseType = {'None':								        {'id':u'-1'},
#                 'Standards':								{'id':u'192644'},
#                 'HW Problem':                               {'id':u'192645'},
#                 '3rd Party Products':                       {'id':u'192646'},
#                 'Missing Requirement':                      {'id':u'192647'},
#                 'Incorrect Requirements':                   {'id':u'192648'},
#                 'Unclear Requirements':                     {'id':u'192649'},
#                 'Changing Requirements':                    {'id':u'192650'},
#                 'Feature Interaction':                      {'id':u'192651'},
#                 'Design Deficiency':                        {'id':u'192652'},
#                 'Lack of Design Detail':                    {'id':u'192653'},
#                 'Defective Fix':                            {'id':u'192654'},
#                 'Feature  Enhancement':                     {'id':u'192655'},
#                 'Code Standards':                           {'id':u'192656'},
#                 'Configuration Mgmt - Merge':               {'id':u'192658'},
#                 'Documentation Issue':                      {'id':u'192659'},
#                 'Dependencies from Other Documentation':    {'id':u'192660'},
#                 'Code Error':                               {'id':u'192661'},
#                 'Code Complexity':                          {'id':u'192662'}
#                 }
#
# EdaCauseType = {
#                 'None':								                       {'id':u'-1'},
#                 'Traceability to Requirements':							   {'id':u'193960'},
#                 'incorrect Testcase':                                      {'id':u'193961'},
#                 'Scenario Not predicted - Customer Specific Test Scope':   {'id':u'193962'},
#                 'Module/Unit tests - Test Scope':                          {'id':u'193963'},
#                 'Entity/Feature Tests - Test Scope':                       {'id':u'193964'},
#                 'Regression Tests -Test Scope':                            {'id':u'193965'},
#                 'Network Verification  -- Test Scope':                     {'id':u'193966'},
#                 'Solution Verification - Test Scope':                      {'id':u'193967'},
#                 'Performance - Test Scope':                                {'id':u'193968'},
#                 'Non-Functianl  - Test Scope':                             {'id':u'193969'},
#                 'Maintenance Test Scope':                                  {'id':u'193970'},
#                 'E2E  Verification -- Test Scope':                         {'id':u'193971'},
#                 'Test Plan':                                               {'id':u'193972'},
#                 'Test Strategy --  Content missing/not covered/Configuration not tested': {'id':u'193973'},
#                 'Missing Test case review':                                {'id':u'193974'},
#                 'Unknown/Unclear test configurations':                     {'id':u'193975'},
#                 'Unforeseen upgrade Paths':                                {'id':u'193976'},
#                 'Unclear Load Model':                                {'id':u'193977'},
#                 'Missing Compatibility Tests':                       {'id':u'193978'},
#                 'Code review missed':                                {'id':u'193979'},
#                 'Configuration missing/misunderstood/incomplete':              {'id':u'219275'},
#                 'Scenario missing/misunderstood/incomplete':                   {'id':u'219276'},
#                 'Extraordinary scenario - Very difficult to recreate defect':  {'id':u'219277'},
#                 'Customer documentation not reviewed/tested':                  {'id':u'219278'},
#                 'Functional Testcase missing/misunderstood/incomplete':        {'id':u'219279'},
#                 'Non-Functional Testcase missing/misunderstood/incomplete':    {'id':u'219280'},
#                 'Regression Testcase missing/misunderstood/incomplete':        {'id':u'219281'},
#                 'Robustness Testcase missing/misunderstood/incomplete':        {'id':u'219282'},
#                 'Test Blocked : Lack of Hardware/Test Tools':                  {'id':u'219283'},
#                 'Test Blocked : Needed SW not available':                      {'id':u'219284'},
#                 'Test run too early in the release':                           {'id':u'219285'},
#                 'Planned Test run post delivery':                              {'id':u'219286'},
#                 'Planned Test not run':                                {'id':u'219287'},
#                 'Out of Testing Scope':                                {'id':u'219288'},
#                 'insufficient testing of changes/fixes':                                {'id':u'219289'},
#                 'insufficient test duration/iterations':                                {'id':u'219290'},
#                 'Fix was available but was not delivered':                              {'id':u'219291'},
#                 'incorrect analysis of test result, marked passed when actually failed': {'id':u'219292'},
#                 'intermittent defect':                                  {'id':u'219293'}}


#JiraSubTask Case Type
JiraSubTaskCaseType = {'RCA':u'219575','EDA':u'219576','RCA and EDA':'219892'}
#Analysis subtask:19800,Action for RCA:19804,Action for EDA:19806
JiraChildIssueType = {'Analysis subtask':u'19800','Action for RCA':u'19804','Action for EDA':u'19806'}

JiraChildIssueType ={'RCA':u'19804','EDA':u'19806'}

JiraUserName = 'Ca_AutomationAccount'
JiraPassWord= 'jira123'
def getjira():
    options = {'server': 'https://jiradc.int.net.nokia.com/'}
    _conn_status = True
    _conn_retry_count = 0
    while _conn_status:
        try:
            _conn_status = False
            print 'Connecting JIRA...'
            jira = JIRA(options, basic_auth=(JiraUserName, JiraPassWord))
            return jira
        except:
            _conn_retry_count += 1
            print ("_conn_retry_count=%d" % _conn_retry_count)
        print 'ProntoDb connecting Error'
        time.sleep(10)
        contiue


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



# FC mapping table
addr_dict = {}
addr_dict['chenlong'] = {'email': 'loong.chen@nokia-sbell.com', 'fc': 'chengbin.qi@nokia-sbell.com'}
addr_dict['yangjinyong'] = {'email': 'jinyong.yang@nokia-sbell.com', 'fc': 'joseph.zhou@nokia-sbell.com'}
addr_dict['zhangyijie'] = {'email': 'frank.han@nokia-sbell.com', 'fc': 'zhilong.jiang@nokia-sbell.com'}
addr_dict['lanshenghai'] = {'email': 'shenghai.lan@nokia-sbell.com', 'fc': 'linggang.tu@nokia-sbell.com'}
addr_dict['liumingjing'] = {'email': 'mingjing.liu@nokia-sbell.com', 'fc': 'zhihua.xu@nokia-sbell.com'}
addr_dict['lizhongyuan'] = {'email': 'zhongyuan.y.li@nokia-sbell.com', 'fc': 'yu.tan@nokia-sbell.com'}
# addr_dict['leienqing']={'email':'enqing.lei@nokia-sbell.com','fc':'chengbin.qi@nokia-sbell.com'}
addr_dict['caizhichao'] = {'email': 'zhi_chao.cai@nokia-sbell.com', 'fc': 'zhi_chao.cai@nokia-sbell.com'}
addr_dict['hujun'] = {'email': 'jun-julian.hu@nokia-sbell.com', 'fc': 'jun-julian.hu@nokia-sbell.com'}
addr_dict['xiezhen'] = {'email': 'jason.xie@nokia-sbell.com', 'fc': 'fei-kevin.liu@nokia-sbell.com'}
addr_dict['wangli'] = {'email': 'li-daniel.wang@nokia-sbell.com',
                       'fc': 'yuan_xing.wu@nokia-sbell.com,jun-julian.hu@nokia-sbell.com'}

addr_dict1 = {}
addr_dict1['loong.chen@nokia-sbell.com'] = 'chenlong'
addr_dict1['jinyong.yang@nokia-sbell.com'] = 'yangjinyong'
addr_dict1['frank.han@nokia-sbell.com'] = 'zhangyijie'
addr_dict1['shenghai.lan@nokia-sbell.com'] = 'lanshenghai'
addr_dict1['mingjing.liu@nokia-sbell.com'] = 'liumingjing'
addr_dict1['zhongyuan.y.li@nokia-sbell.com'] = 'lizhongyuan'
addr_dict1['zhi_chao.cai@nokia-sbell.com'] = 'caizhichao'
addr_dict1['jason.xie@nokia-sbell.com'] = 'xiezhen'
addr_dict1['li-daniel.wang@nokia-sbell.com'] = 'wangli'




internal_task_dict={}
internal_task_dict['chenlong']={}
internal_task_dict['zhangyijie']={}
internal_task_dict['lanshenghai']={}
internal_task_dict['lizhongyuan']={}
internal_task_dict['xiezhen']={}
internal_task_dict['caizhichao']={}
internal_task_dict['yangjinyong']={}
internal_task_dict['liumingjing']={}
internal_task_dict['hujun']={}
internal_task_dict['wangli']={}

task_status_dict={}
task_status_dict['chenlong']=[]
task_status_dict['zhangyijie']=[]
task_status_dict['lanshenghai']=[]
task_status_dict['lizhongyuan']=[]
task_status_dict['xiezhen']=[]
task_status_dict['caizhichao']=[]
task_status_dict['yangjinyong']=[]
task_status_dict['liumingjing']=[]
task_status_dict['hujun']=[]
task_status_dict['wangli']=[]

internal_task_dict1={}
internal_task_dict1['chenlong']={}
internal_task_dict1['zhangyijie']={}
internal_task_dict1['lanshenghai']={}
internal_task_dict1['lizhongyuan']={}
internal_task_dict1['xiezhen']={}
internal_task_dict1['caizhichao']={}
internal_task_dict1['yangjinyong']={}
internal_task_dict1['liumingjing']={}
internal_task_dict1['hujun']={}
internal_task_dict1['wangli']={}

task_status_dict1={}
task_status_dict1['chenlong']=[]
task_status_dict1['zhangyijie']=[]
task_status_dict1['lanshenghai']=[]
task_status_dict1['lizhongyuan']=[]
task_status_dict1['xiezhen']=[]
task_status_dict1['caizhichao']=[]
task_status_dict1['yangjinyong']=[]
task_status_dict1['liumingjing']=[]
task_status_dict1['hujun']=[]
task_status_dict1['wangli']=[]

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
internal_task_dict2['hujun']={}
internal_task_dict2['wangli']={}

task_status_dict2={}
task_status_dict2['chenlong']=[]
task_status_dict2['zhangyijie']=[]
task_status_dict2['lanshenghai']=[]
task_status_dict2['lizhongyuan']=[]
task_status_dict2['xiezhen']=[]
task_status_dict2['caizhichao']=[]
task_status_dict2['yangjinyong']=[]
task_status_dict2['liumingjing']=[]
task_status_dict2['hujun']=[]
task_status_dict2['wangli']=[]


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