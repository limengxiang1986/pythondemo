class A(object):
    nameaa = ''
    def __init__(self):
        self.nameaa = 'aa'

    def funca(self):
        print('function a %s' % self.nameaa)


class B(A):
    def __init__(self):
        self.namebb = 'bb'
        super(B, self).__init__()    #use parent init function
    def funcb(self):
        print('function b %s' % self.namebb)

if __name__ == '__main__':
    b = B()
    b.funca()
    b.funcb()

