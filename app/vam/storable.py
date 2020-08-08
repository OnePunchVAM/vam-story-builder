import copy


class Storable(object):
    def __init__(self, data):
        self.data = data

    def build(self):
        data = copy.deepcopy(self.data)
        return data

    def copy(self):
        return Storable(self.build())

    def merge(self, data):
        self.data.update(data)
