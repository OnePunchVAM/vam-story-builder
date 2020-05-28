import os
import copy
import json

from .atom import Atom


class Scene(object):
    def __init__(self, data, dialog=None):
        self.data = data
        self.dialog = dialog
        self.atoms = {atom.get('id'): Atom(atom) for atom in self.data['atoms']}

    @staticmethod
    def load(filepath):
        if not os.path.isfile(filepath):
            raise FileNotFoundError()
        return Scene(json.load(open(filepath, 'r')))

    def build(self):
        data = copy.deepcopy(self.data)
        data['atoms'] = [atom.build() for atom in self.atoms.values()]
        return data

    def copy(self):
        return Scene(self.build())

    def merge(self, data):
        self.data.update(data)

    def pack(self, atoms):
        for atom_id, atom in atoms.items():
            if not self.atoms.get(atom_id):
                self.atoms.update({atom_id: atom})
