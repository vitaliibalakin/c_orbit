
class Test:
    def __init__(self):
        self.choose = {'test': self.test_, 'test2': self.test2_}
        self.choose['test']('vz', **{'test': 'string'})

    def test_(self, arg, **kwargs):
        print(arg)
        print(kwargs)

    def test2_(self, arg, **kwargs):
        print(arg)
        print(kwargs)


T = Test()
