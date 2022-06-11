
def testFind():
    stra = '123_asdf_dfsk'
    print('rfind:'+str(stra.rfind('_')))
    print('find:'+str(stra.find('_')))
    print('index:'+str(stra.rindex('_',-5)))
    print('index:'+str(stra.index('_',-5)))

def lastIndex():
    stra = '123_asdf_dfsk'
    print('rfind:'+str(stra.rfind('_')))


if __name__ == '__main__':
    lastIndex()




