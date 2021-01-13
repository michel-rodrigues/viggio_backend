
class FakeDBView:
    def __init__(self, obj):
        self.obj = obj

    def __call__(self, obj_id=None):
        return self.obj
