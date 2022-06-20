#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import sys
import json
# import time
# from datetime import datetime
# import traceback
from jira import JIRA

# sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'q-metrics'))
# from performance.perfmanager import PerfManager
# from passwd_protecter.encryption import PasswdEncryp
# from pymagic.timestring import later

# SCRIPT_PATH = os.path.dirname(__file__)


class API2JIRADC(object):
    __jira_server = "https://jiradc.ext.net.nokia.com"
    __cookies = None

    def __init__(self, project, credential, perf=50):   #__init__(self, project, credential: (str, str), perf=50):
        print('Instantiate %s' % self.__class__.__name__)
        # self.__fn_credential = os.path.join(os.path.dirname(__file__), "../rcasharkpasswd.txt")
        # self.__crypt = PasswdEncryp()
        # self.__crypt.loadfromfile(self.__fn_credential)
        # self.__perfm = PerfManager(perf, target=self.__class__.__name__)
        auth = (credential[0], credential[1])
        jira = JIRA(basic_auth=auth, options={'server': 'https://jiradc.ext.net.nokia.com'})
        self.__project = project
        self.__jira = jira

    def __del__(self):
        print('Delete the object of %s' % self.__class__.__name__)

    def get_issuebyjkey(self, jkey):
        # self.__perfm.accupdate()

        issue = None
        try:
            response = self.__jira.search_issues('key={}'.format(jkey), json_result=True)
            if not response:
                raise RuntimeError('Failed to get response from {}'.format(self.__jira.JIRA_BASE_URL))
            elif response['total'] > 0:
                issue = response['issues'][0]
        except Exception as e:
            print('Failed in searching %s. Exception: %s' % (jkey, repr(e)))

        return issue

    # def get_issuesbykeys(self, jkeys:list, basetime=None, discardexception=False):
    #     batchsize = 25
    #     total = len(jkeys)
    #     index = 0
    #     issues = []
    #     while index * batchsize < total:
    #         # self.__perfm.accupdate()  # Performance Management
    #
    #         jql_jkeys = ' OR '.join(
    #             ['key={}'.format(j) for j in jkeys[index * batchsize: min((index + 1) * batchsize, total)]])
    #         if basetime:
    #             jql_expr = '({}) AND updated >= \"{}\"'.format(jql_jkeys, basetime)
    #         else:
    #             jql_expr = '({})'.format(jql_jkeys)
    #         print('[%2d] Try to query with JQL=\"%s\"' % (index + 1, jql_expr))
    #
    #         try:
    #             response = self.__jira.search_issues(jql_expr, json_result=True)
    #             if not response:
    #                 raise RuntimeError('Failed to get response from {}'.format(self.__jira.JIRA_BASE_URL))
    #             elif response['total'] > 0:
    #                 issues.extend(response['issues'])
    #         except Exception as e:
    #             print('Failed in searching multi-key. Exception: %s' % (repr(e)))
    #             if not discardexception:
    #                 if e.status_code == 400:
    #                     issues.append(e.text)
    #
    #         index += 1
    #
    #     return issues

    def query_issues(self, jqcond):
        issues = []
        if 'project' not in jqcond:
            jqcond = 'project = \"%s\" AND %s' % (self.__project, jqcond)

        startat = 0
        total = 1
        while startat < total:
            # self.__perfm.accupdate()
            response = self.__jira.search_issues(jqcond, json_result=True, startAt=startat)
            if not response:
                raise RuntimeError('Failed to get response from {}'.format(self.__jira.JIRA_BASE_URL))
            else:
                startat += response['maxResults']
                total = response['total']
                if response['total'] > 0:
                    issues.extend(response['issues'])

        return issues

    @property
    def jira(self):
        return self.__jira

