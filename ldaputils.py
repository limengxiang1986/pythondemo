import ldap

from commonmodel import UserModel


def loadUserModel(displayName='',email='',uid=''):
    if displayName:
        AssignTo = displayName.strip()
        if displayName == '':
            return UserModel('','','','','')
        try:
            conn = get_ldap_connection()
        except:
            return UserModel('','','','','')
        filter = '(displayName=*%s*)' % displayName
    elif email:
        email = email.strip()
        if email == '':
            return UserModel('','','','','')
        try:
            conn = get_ldap_connection()
        except:
            return UserModel('','','','','')
        filter = '(mail=%s)' % email
    elif uid:
        uid = uid.strip()
        if uid == '':
            return UserModel('','','','','')
        try:
            conn = get_ldap_connection()
        except:
            return UserModel('','','','','')
        filter = '(uid=%s)' % uid
    attrs = ['sn', 'mail', 'cn', 'displayName', 'nsnManagerAccountName','uid']
    base_dn = 'o=NSN'
    # conn = app.config['ldap']
    try:
        result = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)
    except:
        print 'No such account!!!'
        AssignTo = ''
        return AssignTo
    try:
        # AssignTo = result[0][1]['uid'][0]
        displayName1 = result[0][1]['displayName'][0]
        lineManagerAccountId = result[0][1]['nsnManagerAccountName'][0]
        filter = '(uid=%s)' % lineManagerAccountId
        attrs = ['sn', 'mail', 'cn', 'displayName', 'nsnManagerAccountName',uid]
        base_dn = 'o=NSN'
        lineResult = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)
        # lineManagerDisplayName = lineResult[0][1]['displayName'][0]
        lineManagerEmail = lineResult[0][1]['mail'][0]
        u = UserModel(displayName1,result[0][1]['mail'][0],lineManagerEmail,'',result[0][1]['uid'][0])
        lineManagerEmail, squadGroupName, lineDisplayName, tribeLeadDisplayName, tribeName,tribeLeadEmail = getSquadTribeInfoWithConn(u.email, conn)
        u.linemanagerDisplayName = lineDisplayName
        u.linemanagerEmail = lineManagerEmail
        u.squadGroupName = squadGroupName
        u.tribeLeadDisplayName = tribeLeadDisplayName
        u.tribeLeadEmail = tribeLeadEmail
        u.tribename = tribeName
    except:
        if not u:
            u = UserModel(displayName,email,uid=uid)
    return u


def get_ldap_connection():
    # conn = ldap.initialize(app.config['LDAP_PROVIDER_URL'])
    try:
        conn = ldap.initialize('ldap://ed-p-gl.emea.nsn-net.net')
        conn.simple_bind_s('cn=BOOTMAN_Acc,ou=SystemUsers,ou=Accounts,o=NSN', 'Eq4ZVLXqMbKbD4th')
    except:
        pass

    return conn



def getSquadTribeInfoWithConn(JiraIssueAssignee, conn):
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
    # print "JiraIssueAssignee = %s" %JiraIssueAssignee
    result = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)
    mail=''
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
    if 'mail' in result[0][1].keys():
        mail = result[0][1]['mail'][0]
    else:
        mail = ''
    if 'nsnTeamName' in result[0][1].keys():
        squadGroupName = result[0][1]['nsnTeamName'][0]
        # nsnTeamName=result[0][1]['nsnOperativeOrgName'][0]
    else:
        squadGroupName = 'External People'
    if 'nsnManagerAccountName' in result[0][1].keys():
        lineManagerAccountId = result[0][1]['nsnManagerAccountName'][0]
    else:
        print 'JiraAssigneeEmail=%s' % JiraIssueAssignee
        return '', squadGroupName, '', '', '',''
    if len(title.split('Tribe Lead')) > 1 or len(title.split('Head of')) > 1:
    # if title in ['Tribe Leader', 'R&D Tribe Leader']:
        # lineDisplayName = lineDisplayName1
        # tribeLeadDisplayName = displayName
        tribeName = squadGroupName
        # lineManagerEmail = lineManagerEmail1
        return '', squadGroupName, '', '', tribeName,''

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
        return lineManagerEmail1, squadGroupName, lineDisplayName1, '', '',''

    # if title1 in ['Tribe Leader', 'R&D Tribe Leader','Head of NM RD UTF']:
    if len(title1.split('Tribe Lead')) > 1 or len(title1.split('Head of')) > 1:
        # lineDisplayName = lineDisplayName1
        # tribeLeadDisplayName = displayName
        tribeName = squadGroupName1
        # lineManagerEmail = lineManagerEmail1
        return lineManagerEmail1, squadGroupName, lineDisplayName1, lineDisplayName1, tribeName,lineManagerEmail1
    # if title == 'Squad Group Lead':
    if len(title.split('Squad Group Lead')) > 1 or len(title.split('R&D Leader')) > 1:
    # if title == 'Squad Group Lead':
        tribeName = squadGroupName1
        tribeLeadDisplayName = lineDisplayName1
        lineManagerEmail = lineManagerEmail1
        lineDisplayName = lineDisplayName1
        return lineManagerEmail, squadGroupName, lineDisplayName, tribeLeadDisplayName, tribeName,lineManagerEmail
    if len(title.split('Tribe Lead')) > 1 or len(title.split('Head of')) > 1:
    # if title in ['Tribe Leader', 'R&D Tribe Leader']:
        lineDisplayName = lineDisplayName1
        tribeLeadDisplayName = displayName
        tribeName = squadGroupName
        lineManagerEmail = lineManagerEmail1
        return lineManagerEmail, squadGroupName, lineDisplayName, tribeLeadDisplayName, tribeName,mail
    if len(title.split('Tribe Lead')) == 1 and len(title.split('Head of')) == 1 and \
        len(title.split('Squad Group Lead')) == 1 and len(title.split('R&D Leader')) == 1:
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
        tribeEmail = TribeLeadResult[0][1]['mail'][0]
        lineManagerEmail = lineManagerEmail1
        lineDisplayName = lineDisplayName1
        return lineManagerEmail, squadGroupName, lineDisplayName, tribeLeadDisplayName, tribeName,tribeEmail




if __name__ == '__main__':
    u = loadUserModel(
        # displayName='Lei, Enqing (NSB - CN/Hangzhou)' #,
        email='enqing.lei@nokia-sbell.com')
    print(str(u))
    u1 = loadUserModel(
        # displayName='Lei, Enqing (NSB - CN/Hangzhou)' #,
        email='loong.chen@nokia-sbell.com')
    print(str(u1))
    u2 = loadUserModel(
        # displayName='Lei, Enqing (NSB - CN/Hangzhou)' #,
        email='zhuofei.chen@nokia-sbell.com')
    print(str(u2))
    u3 = loadUserModel(
        # displayName='Lei, Enqing (NSB - CN/Hangzhou)' #,
        email='janne.heinonen@nokia.com')
    print(str(u3))

    # print(len('adflksafdcccc'.split('cccc')))

