import traceback

import ldap


class API2LDAP(object):
    def __init__(self, url, passwd):   #__init__(self, project, credential: (str, str), perf=50):
        print('Instantiate %s' % self.__class__.__name__)
        conn = ldap.initialize(url)
        conn.simple_bind_s('cn=BOOTMAN_Acc,ou=SystemUsers,ou=Accounts,o=NSN', passwd)
        self.__ldapconn = conn

    def search(self, filter):
        attrs = ['sn', 'mail', 'cn', 'displayName', 'nsnManagerAccountName', 'uid']
        base_dn = 'o=NSN'
        try:
            result = self.__ldapconn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)
        except:
            result = None
            print('error' + traceback.format_exc())
        return result


