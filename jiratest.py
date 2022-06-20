import os

from mnrcaapi.mnrcaapi import MNRCAAPIService


def testjira():
    fn_credential = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                 "q-metrics/passwd_protecter/rcasharkpasswd.txt")
    mnrca = MNRCAAPIService(('rcashark', 'Jira4321'))
    # print(mnrca.__ldapconn)
    # mnrca.update_field('MNRCA-46699',
    #                    {'Summary': '01309318:No user plane traffic in LTE TDD (legacy case ref 00679635)'})

    # issue1 = mnrca.get_issuebykey('MNRCA-52029')
    # print(issue1)
    # ret = mnrca.update_fields('MNRCA-52029', {'Summary': 'EDA Action For 01309318',
    #                                           'Assignee Account': 'qmxh38',
    #                                           'Proposed Action (EDA)': 'Add UT case(s) to cover the scenario',
    #                                           'Action Proposal EDA': 'Unit Test Improvement',
    #                                           'Escape Cause': 'Code_Analysis_Tools',    #'UT uncover',
    #                                           'Escape Cause Category': 'Unit_Tests',    #'Unit Test',
    #                                           # 'Escape Cause SubCategory': 'Code not covered by test',
    #                                           'EDA Action Target': '2022-10-24'})
    # print('ret = %s' % ret)

    ret = mnrca.update_fields('MNRCA-52174', {'Summary': 'RCA Action For 01309318',
                                              'Assignee Account': 'qmxh38',
                                              'Proposed Action (RCA)': 'Lesson learn workshop including:\n'
                                                                       '1) PR background\n'
                                                                       '2) algorithm introduction\n'
                                                                       '3) lesson learn\n'
                                                                       '4) PoC process.',
                                              'Action Proposal RCA': 'Low-Level Design Improvement',
                                              'Root Cause': 'No PoC before implementation',
                                              'Root Cause Category': 'Low_Level_Design',
                                              'Root Cause SubCategory': 'Low level design missing/gap',
                                              'RCA Action Target': '2022-10-24'})
    print('ret = %s' % ret)

    # mnrca.assign('MNRCA-51741', 'jzhi')

