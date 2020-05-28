import copy

from .storable import Storable


class Atom(object):
    def __init__(self, data):
        self.data = data
        self.storables = {data.get('id'): Storable(data) for data in self.data['storables']}

    def build(self):
        data = copy.deepcopy(self.data)
        data['storables'] = [storable.build() for storable in self.storables.values()]
        return data

    def copy(self):
        return Atom(self.build())

    def merge(self, data):
        self.data.update(data)
