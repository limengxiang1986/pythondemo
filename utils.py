import copy


def testFind():
    stra = '123_asdf_dfsk'
    print('rfind:'+str(stra.rfind('_')))
    print('find:'+str(stra.find('_')))
    print('index:'+str(stra.rindex('_',-5)))
    print('index:'+str(stra.index('_',-5)))

def lastIndex():
    stra = '123_asdf_dfsk'
    print('rfind:'+str(stra.rfind('_')))

def lastStr(strp,split):
    if not strp or not split:
        return ''
    return str(strp[strp.rfind(split)+1:])

def findStr(strl,strr,caseSensitive=True):
    if not strl or not strr:
        return False
    if caseSensitive:
        return True if strl.find(strr) > -1 else False
    else :
        return True if strl.lower().find(strr.lower()) > -1 else False

def copyObj(obj):
    return copy.copy(obj)

if __name__ == '__main__':
    # lastIndex()
    rest = lastStr('asdf','_')
    print(rest)
    # print('Abcdbc'.lower().find('abc'.lower()))
    print(findStr('A','a'))
    print(findStr('A','a',False))
    print(findStr('A','A'))
    print(findStr('A','A',False))
    print(str(None))
    obj1 = {'a': 'asdf'}
    obj2 = copyObj(obj1)
    print('obj1:'+str(id(obj1)) + ', obj2:'+ str(id(obj2)))



