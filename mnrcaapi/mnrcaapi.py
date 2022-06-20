#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import sys
import json

# import time
# from datetime import datetime
# import traceback
sys.path.append(os.path.dirname(__file__))
from restapi2jiradc import API2JIRADC
from restapi2ldap import API2LDAP



class MNRCAAPIService(API2JIRADC):
    def __init__(self, credential, perf=50):    #__init__(self, credential: (str, str), perf=50):
        print('Instantiate %s' % self.__class__.__base__.__name__)
        self.__project = 'MNRCA'
        super(MNRCAAPIService, self).__init__(self.__project, credential, perf=perf)
        self.__ldapconn = API2LDAP('ldap://ed-p-gl.emea.nsn-net.net','Eq4ZVLXqMbKbD4th')

    # def __del__(self):
    #     super().__del__()
    #     print('Delete the object of %s' % self.__class__.__base__.__name__)

    def ldap_search(self,email='',displayName='',uid=''):
        self.__ldapconn.search()

    SUPPOERTED_EDITABLE_FIELDS = [
        {'Type': ['Action for RCA'],
         'fieldmaps': [('Summary', 'summary'),
                       ('Assignee Account', 'assignee', 'name'),
                       ('Proposed Action (RCA)', 'customfield_37480'),
                       ('Action Proposal RCA', 'customfield_37543', 'value'),
                       ('Action Proposal RCA #ID', 'customfield_37543', 'id'),
                       ('Root Cause', 'customfield_37755'),
                       ('Root Cause Category', 'customfield_37541', 'value'),
                       ('Root Cause Category #ID', 'customfield_37541', 'id'),
                       ('Root Cause SubCategory', 'customfield_37541', 'child', 'value'),
                       ('Root Cause SubCategory #ID', 'customfield_37541', 'child', 'id'),
                       ('RCA Action Target', 'customfield_37070')]
         },
        {'Type': ['Action for EDA'],
         'fieldmaps': [('Summary', 'summary'),
                       ('Assignee Account', 'assignee', 'name'),
                       ('Proposed Action (EDA)', 'customfield_37472'),
                       ('Action Proposal EDA', 'customfield_38092', 'value'),
                       ('Action Proposal EDA #ID', 'customfield_38092', 'id'),
                       ('Escape Cause', 'customfield_37470'),
                       ('Escape Cause Category', 'customfield_37615', 'value'),
                       ('Escape Cause Category #ID', 'customfield_37615', 'id'),
                       ('Escape Cause SubCategory', 'customfield_37615', 'child', 'value'),
                       ('Escape Cause SubCategory #ID', 'customfield_37615', 'child', 'id'),
                       ('EDA Action Target', 'customfield_37058')]
         }
    ]

    ID_RCAACTION_TYPES = [('-1', None),
                          ("236225", "Requirements Improvement"),
                          ("236226", "Architecture Improvement"),
                          ("236227", "High-Level Design Improvement"),
                          ("236228", "Low-Level Design Improvment"),
                          ("236228", "Low-Level Design Improvement"),
                          ("236229", "Coding Quality Improvement"),
                          ("236230", "User Documentation (including Release Note) Improvement"),
                          ("236231", "Configuration and Fault Management Improvement"),
                          ("236232", "Knowledge/ Expertise/ Training Improvement"),
                          ("280110", "Diagnostics Improvement"),
                          ]

    ID_ROOTCAUSE_CATEGORIES = [("",None),
                               ("236010", "Requirements"),
                               ("236011", "Architecture "),
                               ("236012", "High-Level Design"),
                               ("236013", "Low-Level Design"),
                               ("236014", "Code "),
                               ("236015", "User Documentation  (including Release Notes)"),
                               ("236016", "Configuration and Fault Management"),
                               ("236017", "Collaboration with Suppliers"),
                               ]
    ID_EDAACTION_TYPES = [('-1', None),
                          ("236233", 'Technical Reviews Improvement'),
                          ("236234", 'Code Analysis Tools Improvement'),
                          ("236235", 'Unit Test Improvement'),
                          ("236236", 'System Component / Module Test Improvment'),
                          ("236236", 'System Component / Module Test Improvement'),
                          ("236237", 'Entity/ Integration and Verification Test Improvement'),
                          ("236237", 'Entity / Integration and Verification Test Improvement'),
                          ("236238", 'System Verification Function Test Improvement'),
                          ("236238", 'System Verification Functional Test Improvement'),
                          ("236239", 'System Verification Non-Functional Testing Improvement'),
                          ("236239", 'System Verification Non - Functional Testing Improvement'),
                          ("318710", 'Test Strategy/WoW Improvement'),
                          ]
    ID_ESCAPECAUSE_CATEGORIES = [('-1',None),
                                 ('236241', 'Code Analysis Tools'),
                                 ('236242', 'Unit Test'),
                                 ('236243', 'System Component / Module Test'),
                                 ('236244', 'Entity/ Integration and Verification Test'),
                                 ('236245', 'System Verification Function Test'),
                                 ('236245', 'System Verification Functional Test'),
                                 ('236246', 'System verification Non-Functional Testing'),
                                 ('236247', 'Collaboration with Suppliers'),
                                ('236241',  'Code_Analysis_Tools'),
                                ('236242', 'Unit_Tests'),
                                ('236243',  'System_Component_or_Module_Test'),
                                ('236244',  'Entity_or_Integration_and_Verification_Test'),
                                ('236245',  'System_Verification_Functional_Test'),
                                ('236246',  'System_verification_Non_Functional_Testing'),
                                ('236247', 'Collaborated_Mode_with_Suppliers'),
    ]

    ID_ROOTCAUSE_SUBCATEGORIES = [
        ('236035', '3rd Party compatibility / interoperability'),
        ('236068', '3rd party software limitations'),
        ('236031', 'Architecture gap'),
        ('236032', 'Arcitecture specification error'),
        ('236057', 'Build error/ incorrect version'),
        ('236028', 'CPU overload error'),
        ('236018', 'Changing Requirement'),
        ('236045', 'Code language knowledge/expertise'),
        ('236043', 'Code too complex'),
        ('236044', 'Coding logic error'),
        ('236046', 'Coding standards violations'),
        ('236019', 'Customer specific Configuration/traffic requirements not accounted for'),
        ('236041', 'Deficient design/ design Error'),
        ('236061', 'Delivery failure'),
        ('236038', 'Design error'),
        ('236042', 'Design knowledge, skills, competence (timer management, buffer handling, etc.)'),
        ('236063', 'Documentation failure'),
        ('236034', 'Hardware compatibility'),
        ('236037', 'High level design missing/gap'),
        ('236048', 'Implementation error'),
        ('236064', 'Implementation failure'),
        ('236047', 'Implementation missing'),
        ('236055', 'Inconsistency within the same customer document'),
        ('236021', 'Incorrect Requirement'),
        ('236054', 'Incorrect information in the change note'),
        ('236049', 'Incorrect information used to create End-User Documentation'),
        ('236026', 'Interworking error -  feature or component interaction.'),
        ('236062', 'Lack of specification'),
        ('236065', 'Lack of testing'),
        ('236053', 'Language error'),
        ('236024', 'Late added Feature(s)'),
        ('236036', 'Legacy interaction error'),
        ('236040', 'Low level design missing/gap'),
        ('236027', 'Memory consumption error'),
        ('236058', 'Merge error'),
        ('236059', 'Missed defect inheritance or porting process error'),
        ('236020', 'Missing Requirement'),
        ('236050', 'Missing content/ step in procedure'),
        ('236051', 'Missing detailed content (delivered content not sufficient from user PoV)'),
        ('236066', 'Missing requirement'),
        ('236023', 'Misunderstood Customer Requirement'),
        ('236052', 'Outdated content'),
        ('236067', 'Project management'),
        ('236029', 'Software robustness error'),
        ('236030', 'Stability error'),
        ('236025', 'Standards Interpretation Error'),
        ('236022', 'Unclear Requirement'),
        ('236056', 'User documentation not tested'),
        ('', 'None'),
    ]
    ID_ESCAPECAUSE_SUBCATEGORIES = [
        ('236018', 'Changing Requirement'),
        ('236019', 'Customer specific Configuration/traffic requirements not accounted for'),
        ('236020', 'Missing Requirement'),
        ('236021', 'Incorrect Requirement'),
        ('236022', 'Unclear Requirement'),
        ('236023', 'Misunderstood Customer Requirement'),
        ('236024', 'Late added Feature(s)'),
        ('236025', 'Standards Interpretation Error'),
        ('236026', 'Interworking error -  feature or component interaction.'),
        ('236027', 'Memory consumption error'),
        ('236028', 'CPU overload error'),
        ('236029', 'Software robustness error'),
        ('236030', 'Stability error'),
        ('236031', 'Architecture gap'),
        ('236032', 'Arcitecture specification error'),
        ('236034', 'Hardware compatibility'),
        ('236035', '3rd Party compatibility / interoperability'),
        ('236036', 'Legacy interaction error'),
        ('236037', 'High level design missing/gap'),
        ('236038', 'Design error'),
        ('236040', 'Low level design missing/gap'),
        ('236041', 'Deficient design/ design Error'),
        ('236042', 'Design knowledge, skills, competence (timer management, buffer handling, etc.)'),
        ('236043', 'Code too complex'),
        ('236044', 'Coding logic error'),
        ('236045', 'Code language knowledge/expertise'),
        ('236046', 'Coding standards violations'),
        ('236047', 'Implementation missing'),
        ('236048', 'Implementation error'),
        ('236049', 'Incorrect information used to create End-User Documentation'),
        ('236050', 'Missing content/ step in procedure'),
        ('236051', 'Missing detailed content (delivered content not sufficient from user PoV)'),
        ('236052', 'Outdated content'),
        ('236053', 'Language error'),
        ('236054', 'Incorrect information in the change note'),
        ('236055', 'Inconsistency within the same customer document'),
        ('236056', 'User documentation not tested'),
        ('236057', 'Build error/ incorrect version'),
        ('236058', 'Merge error'),
        ('236059', 'Missed defect inheritance or porting process error'),
        ('236061', 'Delivery failure'),
        ('236062', 'Lack of specification'),
        ('236063', 'Documentation failure'),
        ('236064', 'Implementation failure'),
        ('236065', 'Lack of testing'),
        ('236066', 'Missing requirement'),
        ('236067', 'Project management'),
        ('236068', '3rd party software limitations'),
    ]

    def __map_selection2id(self, key, selection):
        itemid = None
        if key == 'Action Proposal RCA':
            list_IDmap = self.ID_RCAACTION_TYPES
        elif key == 'Root Cause Category':
            list_IDmap = self.ID_ROOTCAUSE_CATEGORIES
        elif key == 'Root Cause SubCategory':
            list_IDmap = self.ID_ROOTCAUSE_SUBCATEGORIES
        elif key == 'Action Proposal EDA':
            list_IDmap = self.ID_EDAACTION_TYPES
        elif key == 'Escape Cause Category':
            list_IDmap = self.ID_ESCAPECAUSE_CATEGORIES
        elif key == 'Escape Cause SubCategory':
            list_IDmap = self.ID_ESCAPECAUSE_SUBCATEGORIES
        else:
            return itemid

        for sel in list_IDmap:
            try:
                selval = sel[1].replace(" ",'').replace('_or_','').replace('_','').replace('/','').replace("-",'') if sel[1] else ''
                selectionval = selection.replace(" ",'').replace('_or_','').replace('_','').replace('/','').replace("-",'') if selection else ''
                if selval == selectionval:
                    itemid = sel[0]
            except:
                pass
        if itemid is None:
            print('Selection item \"%s\" not supported')
        return itemid

    def get_issuebykey(self, jkey):
        return super(MNRCAAPIService, self).get_issuebyjkey(jkey)

    def __map_fieldname(self, issuetype, dictdata):
        keys2rm = []
        dictreplacement = {}
        for key, val in dictdata.items():
            if key in ['Action Proposal RCA', 'Root Cause Category', 'Root Cause SubCategory',
                       'Action Proposal EDA', 'Escape Cause Category', 'Escape Cause SubCategory']:
                itemid = self.__map_selection2id(key, val)
                if itemid:
                    keys2rm.append(key)
                    dictreplacement.update({'{} #ID'.format(key): itemid})
        for key2rm in keys2rm:
            dictdata.pop(key2rm)
        dictdata.update(dictreplacement)

        dictraw = {}
        for key, val in dictdata.items():
            # adjustval = self.__adjustVal(key, val)
            found = False
            for cat in self.SUPPOERTED_EDITABLE_FIELDS:
                if issuetype in cat['Type']:
                    for tupattr in cat['fieldmaps']:
                        if key == tupattr[0]:
                            length = len(tupattr)
                            if length == 2:
                                dictraw.update({tupattr[1]: val})
                            else:
                                assert length > 2, 'Internal Error: Too short attribute tuple %s' % tupattr
                                tmpval = val
                                # tmpval = val
                                for index in range(length, 2, -1):
                                    attr = tupattr[index - 1]
                                    tmpval = {attr: tmpval}
                                if tupattr[1] not in dictraw.keys():
                                    dictraw.update({tupattr[1]: tmpval})
                                else:
                                    tmpval.update(dictraw[tupattr[1]])
                                    dictraw.update({tupattr[1]: tmpval})
                            found = True
                            break
            if not found:
                dictraw.clear()
                dictraw.update({'error': 'Field \"%s\" not supported for type \"%s\"' % (key, issuetype)})
                break
        return dictraw

    # def __adjustVal(self, key, value):
    #     if key == 'Escape Cause Category':
    #         findval = findVal(EdaCauseType, value)
    #         value = findval
    #     elif key == 'Action Proposal EDA':
    #         findval = findVal(EdaActionType, value)
    #         value = findval
    #     elif key == 'Root Cause Category':
    #         findval = findVal(RcaCauseType, value)
    #         value = findval
    #     elif key == 'Action Proposal RCA':
    #         findval = findVal(RcaActionType, value)
    #         value = findval
    #     return value


    def update_fields(self, jirakey, dictdata):
        """
        Update specific fields of issue with key equal to jirakey. Supported fields are list in README.txt.
        Note: Cause Category and SubCategory must be specified simultabeously when udpating any one of both.
        :param jirakey: JIRA key which is intended to update.
        :param dictdata: Fields to be updated. Field names are basically similar to what are displayed in web page.
        :return: False - Nothing is updated becasue no field is specified or some specified fields are not supported.
        """
        if len(dictdata) == 0:
            return False

        issue = self.jira.issue(jirakey)
        dictraw = self.__map_fieldname(issue.fields.issuetype.name, dictdata)
        if 'error' in dictraw.keys():
            print('Error: %s' % dictraw['error'])
            ret = False
        else:
            print('Update:\n%s' % json.dumps(dictraw, indent=4))
            ret = issue.update(fields=dictraw, notify=True)
        return ret

    def assign(self, jirakey, account):
        issue = self.jira.issue(jirakey)
        dictraw = self.__map_fieldname(issue.fields.issuetype.name, {'Assignee Account': account})
        if 'error' in dictraw.keys():
            print('Error: %s' % dictraw['error'])
            ret = False
        else:
            print('Assigned To: %s' % account)
            ret = self.jira.assign_issue(issue, account)
        return ret

# def findVal(dict , key2):
#     for key in dict :
#         adjkey = key.replace(" ",'').replace('_or_','').replace('_','').replace('/','')
#         adjkey2 = key2.replace(" ",'').replace('_or_','').replace('_','').replace('/','')
#         if adjkey == adjkey2:
#             return dict[key]['value']
#     return ''
#
# RcaActionType ={
#     'None':                                                   {'id':u'-1','value':'None'},
#     'Requirements Improvement':                               {'id':u'236225','value':'Requirements Improvement'},
#     'Architecture Improvement':                               {'id':u'236226','value':'Architecture Improvement'},
#     'High-Level Design Improvement':                          {'id':u'236227','value':'High-Level Design Improvement'},
#     'Low-Level Design Improvement':                           {'id':u'236228','value':'Low-Level Design Improvment'},
#     'Low-Level Design Improvment':                            {'id':u'236228','value':'Low-Level Design Improvment'},
#     'Coding Quality Improvement':                             {'id':u'236229','value':'Coding Quality Improvement'},
#     'User Documentation (including Release Note) Improvement':{'id':u'236230','value':'User Documentation (including Release Note) Improvement'},
#     'Configuration and Fault Management Improvement':         {'id':u'236231','value':'Configuration and Fault Management Improvement'},
#     'Knowledge/ Expertise/ Training Improvement':             {'id':u'236232','value':'Knowledge/ Expertise/ Training Improvement'},
#     'Diagnostics Improvement':                                {'id':u'280110','value':'Diagnostics Improvement'},
# }
#
# RcaCauseType ={
#     'None':                                     {'id':u'','value':'None'},
#     'Requirements':                             {'id':u'236010','value':'Requirements'},
#     'Architecture':                             {'id':u'236011','value':'Architecture '},
#     'High_Level_Design':                        {'id':u'236012','value':'High-Level Design'},
#     'Low_Level_Design':                         {'id':u'236013','value':'Low-Level Design '},
#     'Code':                                     {'id':u'236014','value':'Code '},
#     'User_Documentation_including_Release_Note':{'id':u'236015','value':'User Documentation  (including Release Notes)'},
#     'Configuration_and_Fault_Management':       {'id':u'236016','value':'Configuration and Fault Management'},
#     'Collaborated_Mode_with_Suppliers':         {'id':u'236017','value':'Collaboration with Suppliers'},
# }
#
# EdaActionType={
#     'None':                                                     {'id':u'-1'},
#     'Technical Reviews Improvement':                            {'id':u'236233','value':'Technical Reviews Improvement'},
#     'Code Analysis Tools Improvement':                          {'id':u'236234','value':'Code Analysis Tools Improvement'},
#     'Unit Test Improvement':                                    {'id':u'236235','value':'Unit Test Improvement'},
#     'System Component / Module Test Improvement':               {'id':u'236236','value':'System Component / Module Test Improvment'},
#     'Entity/Integration and Verification Test Improvement':     {'id':u'236237','value':'Entity/ Integration and Verification Test Improvement'},
#     'System Verification Functional Test Improvement':          {'id':u'236238','value':'System Verification Functional&nbsp;Test Improvement'},
#     'System Verification Non-Functional Testing Improvement':   {'id':u'236239','value':'System Verification Non-Functional Testing Improvement'},
#     'Test Strategy/WoW Improvement':                            {'id':u'318710','value':'Test Strategy/WoW Improvement'},
# }
#
# EdaCauseType ={
#     'None':                                         {'id':u'','value':''},
#     'Code_Analysis_Tools':                          {'id':u'236241','value':'Code Analysis Tools'},
#     'Unit_Tests':                                   {'id':u'236242','value':'Unit Test'},
#     'System_Component_or_Module_Test':              {'id':u'236243','value':'System Component / Module Test'},
#     'Entity_or_Integration_and_Verification_Test':  {'id':u'236244','value':'Entity/ Integration and Verification Test'},
#     'System_Verification_Functional_Test':          {'id':u'236245','value':'System Verification Functional Test'},
#     'System Verification Function Test':            {'id':u'236245','value':'System Verification Functional Test'},
#     'System Verification Functional Test':          {'id':u'236245','value':'System Verification Functional Test'},
#     'System_verification_Non_Functional_Testing':   {'id':u'236246','value':'System verification Non-Functional Testing'},
#     'Collaborated_Mode_with_Suppliers':             {'id':u'236247','value':'Collaboration with Suppliers'},
#     # 'Technical_Reviews':                            {'id':u'236248','value':'Code Analysis Tools'},
#     # 'None':                                  {'id':u''},
#     # 'TechnicalReviews':                      {'id':u'236248'},
#     # 'CodeAnalysisTools':                     {'id':u'236241'},
#     # 'UnitTest':                              {'id':u'236242'},
#     # 'SystemComponentModuleTest':             {'id':u'236243'},
#     # 'EntityIntegrationAndVerificationTest':  {'id':u'236244'},
#     # 'SystemVerificationFunctionalTest':      {'id':u'236245'},
#     # 'SystemVerificationNonFunctionalTesting':{'id':u'236246'},
#     # 'CollaborationWithSuppliers':            {'id':u'236247'},
# }

# if __name__ == '__mian__':
#     print(findVal(EdaCauseType,'Unit_Tests'))


