import os
import json
import copy
import shutil
import pathlib

from glob import glob

from .vam.scene import Scene
from .vam.atom import Atom
from .dialog import Dialog

import logging

IGNORE_ATOMS = ['AnimationStep']


class Project(object):
    dialog_branch_count_max = 0
    dialog_choice_count_max = 0

    def __init__(self, name, projects_path, templates_path, scenes_path):
        self.name = name

        self.projects_path = projects_path
        if not os.path.isdir(self.projects_path):
            raise FileNotFoundError("Project directory not found!")

        self.templates_path = templates_path
        if not os.path.isdir(self.templates_path):
            raise FileNotFoundError("Template directory not found!")

        self.packages_path = os.path.join(self.templates_path, 'packages')
        if not os.path.isdir(self.packages_path):
            raise FileNotFoundError("Packages directory not found!")

        self.scenes_path = scenes_path
        if not os.path.isdir(self.scenes_path):
            raise FileNotFoundError("Packages directory not found!")

        self.build_path = os.path.join(self.scenes_path, "%s.scaffold" % self.name)
        self.source_path = os.path.join(self.scenes_path, self.name)

        config_filepath = os.path.join(self.projects_path, self.name, 'blueprint.json')
        self.config = json.load(open(config_filepath, 'r'))

    def scaffold(self):
        # Delete existing build path
        if os.path.exists(self.build_path):
            logging.warning("Deleting build path: %s" % self.build_path)
            shutil.rmtree(self.build_path)

        # Copy source files to build path (if applicable)
        if os.path.isdir(self.source_path):
            logging.info("Transferring scene files: %s -> %s" % (self.source_path, self.build_path))
            shutil.copytree(self.source_path, self.build_path)

        # Get all atoms to pack into scenes
        package_atoms = self.get_package_atoms()
        logging.info("Found %d package atoms." % len(package_atoms))

        # Get all scenes required to scaffold
        scenes = self.get_scenes()
        logging.info("Found %d scenes." % len(scenes))

        # Get all dialog branch atoms to prefill scenes with
        dialog_atoms = self.get_dialog_atoms(scenes)
        logging.info("Found %d dialog atoms to add to scenes." % len(dialog_atoms))

        # Prefill scenes with dialog branch atoms
        if len(dialog_atoms):
            logging.info("Pack dialog atoms into scenes..")
            self.pack_scenes(scenes, dialog_atoms)

        # Scan scenes for unspecified atoms (atoms that exist in one scene but not it's siblings)
        backfill_atoms = self.get_backfill_atoms(scenes, package_atoms)
        logging.info("Found %d atoms to backfill into scenes." % len(backfill_atoms))

        # Backfill discovered atoms into scenes
        if len(backfill_atoms):
            logging.info("Pack discovered atoms into scenes..")
            self.pack_scenes(scenes, backfill_atoms)

        # Scan scenes for missing packages and pack them into scenes
        if len(package_atoms):
            logging.info("Scan scenes for missing packages and pack them into scenes..")
            self.pack_scenes(scenes, package_atoms)

            # Generate animation pattern atoms from twinery dialog trees and
            # merge dialog animation patterns into relevant scenes (preserving existing triggers)
            logging.info("Update dialog tree(s), triggers and actions..")
            self.build_dialog(scenes)

        # Save all scenes last
        logging.info("Saving scenes to build path: %s" % self.build_path)
        self.save_scenes(scenes)

    def save_scenes(self, scenes):
        for relative_scene_path, scene in scenes.items():
            scene_path = os.path.join(self.build_path, relative_scene_path)
            scene_path = scene_path.replace('/', os.sep).replace('\\', os.sep)
            pathlib.Path(os.path.dirname(scene_path)).mkdir(parents=True, exist_ok=True)
            json.dump(scene.build(), open(scene_path, 'w'))
            logging.info("Saved scene: %s" % scene_path)

    def pack_scenes(self, scenes, atoms):
        for scene in scenes.values():
            scene.pack(atoms)

    def build_dialog(self, scenes):
        for scene in scenes.values():
            if not scene.dialog:
                continue
            scene.dialog.build(scene)

    def get_dialog_atoms(self, scenes):
        atoms = {}
        self.dialog_branch_count_max = 0
        self.dialog_choice_count_max = 0

        # Determine dialog tree with the most branches and get choice count
        for scene in scenes.values():
            # Skip scenes without dialog attached
            if not scene.dialog:
                continue
            # Get total dialog branches
            scene_atom_count = scene.dialog.get_atom_counts()
            if self.dialog_branch_count_max < scene_atom_count[0]:
                self.dialog_branch_count_max = scene_atom_count[0]
            if self.dialog_choice_count_max < scene_atom_count[1]:
                self.dialog_choice_count_max = scene_atom_count[1]

        # Create dialog containers
        if self.dialog_branch_count_max > 0:
            atoms.update(Dialog.scaffold_containers(self.templates_path))

        # Build scaffolding for dialog branches
        for idx in range(self.dialog_branch_count_max):
            atoms.update(Dialog.scaffold_branch(self.templates_path, idx))

        # Build scaffolding for dialog choices
        for idx in range(self.dialog_choice_count_max):
            atoms.update(Dialog.scaffold_choice(self.templates_path, idx))

        logging.info("Maximum possible dialog branches per scene: %s" % self.dialog_branch_count_max)
        logging.info("Maximum possible dialog choices per scene: %s" % self.dialog_choice_count_max)

        return atoms

    def get_backfill_atoms(self, scenes, package_atoms):
        backfill_atoms = {}
        for scene in scenes.values():
            for atom_id, atom in scene.atoms.items():
                if atom_id not in package_atoms.keys() and atom_id.split('#')[0] not in IGNORE_ATOMS:
                    new_atom = atom.copy()
                    new_atom.data['on'] = 'false'
                    backfill_atoms.update({atom_id: new_atom})
        return backfill_atoms

    def get_package_atoms(self):
        default_atoms_path = os.path.join(self.templates_path, 'default.json')
        atoms = json.load(open(default_atoms_path, 'r'))
        for pkg_name, pkg_count in self.config.get('packages', {}).items():
            atom_name = pkg_name.split('/')[0]
            raw = open(os.path.join(self.packages_path, '%s.json' % pkg_name), 'r').read()
            for idx in range(pkg_count):
                pack_id = atom_name if idx == 0 else '%s#%d' % (atom_name, idx + 1)
                atoms += json.loads(raw.replace('$ID', pack_id))
        return {atom.get('id'): Atom(atom) for atom in atoms}

    def get_scenes(self):
        # Get list of all scenes, both existing and those specified in config
        scene_template = json.load(open(os.path.join(self.templates_path, 'scene.json'), 'r'))
        project_scenes = {}
        for scene in self.config.get('scenes', []):
            if isinstance(scene, str):
                project_scenes.update({scene: {'scene_path': scene}})
            else:
                project_scenes.update({scene.get('scene_path'): scene})
        existing_scene_paths = [y for x in os.walk(self.build_path) for y in glob(os.path.join(x[0], '*.json'))]
        for scene_path in existing_scene_paths:
            rel_scene_path = scene_path.replace(self.build_path + os.sep, '')
            if rel_scene_path not in project_scenes.keys():
                project_scenes.update({rel_scene_path: {'scene_path': rel_scene_path}})
            project_scenes.get(rel_scene_path)['exists'] = True

        # Build out scene objects and corresponding dialog
        scenes = {}
        for scene_path, scene_config in project_scenes.items():
            if not scene_path.lower().endswith('.json'):
                raise Exception("Invalid scene path specified in config: %s" % scene_path)
            dialog = None
            if scene_config.get('dialog_path'):
                dialog_path = os.path.join(self.projects_path, self.name, scene_config.get('dialog_path')) \
                    .replace('/', os.sep).replace('\\', os.sep)
                dialog = Dialog(self.templates_path, dialog_path)
            if scene_config.get('exists'):
                abs_scene_path = os.path.join(self.build_path, scene_path).replace('/', os.sep).replace('\\', os.sep)
                scene_data = json.load(open(abs_scene_path, 'r'))
            else:
                scene_data = copy.deepcopy(scene_template)
            scenes.update({scene_path: Scene(scene_data, dialog)})

        return scenes
