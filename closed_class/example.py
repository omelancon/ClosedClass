from closed_class import ClosedMeta

class MyInt(int, metaclass=ClosedMeta, exceptions=('__sub__', '__int__')):
    pass

x = MyInt(7)
y = MyInt(6)


assert type(x + y) == MyInt
assert type(x.real) == MyInt
assert type(x - y) == int

