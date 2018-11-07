def test(**kwargs):
    for a,b in kwargs.items():
        print(a,b)

test(apple="a", qq=5, ee=11, apple="apple")

def gog(args):
    for arg in args:
        print(arg)

gog(["a", 5, 11, "apple"])
