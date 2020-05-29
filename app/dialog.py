import os
import re
import json
import copy

from .vam.atom import Atom

NAME_PREFIX = 'D'

DEFAULT_START_TIME = 0.1
DEFAULT_DURATION = 2.0
DEFAULT_MESSAGE_BUFFER = 0.4
DEFAULT_PROMPT_BUFFER = 0.2

ATOM_DIALOG = 'Dialog'
ATOM_BRANCH = 'Dialog-Branch'
ATOM_CHOICE = 'Dialog-Choices-Btn'

CHOICE_COLOR = 'BLUE'
CHOICE_STARTING_Y = 1.22
CHOICE_GAP = 0.07
CHOICE_COLORS = {
    'BLACK': {
        "h": "0.1700005",
        "s": "0",
        "v": "0.2029198"
    },
    'TEAL': {
        "h": "0.4894297",
        "s": "0.6444453",
        "v": "0.7410609"
    },
    'GREEN': {
        "h": "0.3586576",
        "s": "0.6444453",
        "v": "0.7410609"
    },
    'RED': {
        "h": "0",
        "s": "0.6444453",
        "v": "0.7410609"
    },
    'PURPLE': {
        "h": "0.7690026",
        "s": "0.6444453",
        "v": "0.7410609"
    },
    'YELLOW': {
        "h": "0.1749429",
        "s": "0.6444453",
        "v": "0.7410609"
    },
    'BLUE': {
        "h": "0.6082565",
        "s": "0.6444453",
        "v": "0.7410609"
    },
    'PINK': {
        "h": "0.8668843",
        "s": "0.6444453",
        "v": "0.7410609"
    }
}


class Dialog(object):
    branch_idx = 0
    branch_count_max = 0
    choice_count_max = 0
    processed_passages = dict()

    def __init__(self, templates_path, dialog_file):
        self.templates_path = templates_path
        if not os.path.isdir(self.templates_path):
            raise FileNotFoundError("Template directory not found!")

        self.data = json.load(open(dialog_file, 'r'))
        passages = self.data.get('passages')
        self.starting_passage = passages[0]
        self.passages = {x.get('name'): x for x in passages[1:]} if len(passages) > 1 else {}

    @staticmethod
    def scaffold_containers(templates_path):
        template = open(os.path.join(templates_path, 'dialog.json'), 'r').read() \
            .replace('$ID', ATOM_DIALOG)
        return {x.get('id'): Atom(x) for x in json.loads(template)}

    @staticmethod
    def scaffold_branch(templates_path, index):
        # Create dialog branch from template
        atom_id = '%s#%d' % (ATOM_BRANCH, index + 1)
        template = open(os.path.join(templates_path, 'dialog_branch.json'), 'r').read() \
            .replace('$ID', atom_id)
        return {x.get('id'): Atom(x) for x in json.loads(template)}

    @staticmethod
    def scaffold_choice(templates_path, index):
        # Create dialog choice from template
        position = CHOICE_STARTING_Y - CHOICE_GAP * index
        atom_id = '%s#%d' % (ATOM_CHOICE, index + 1)
        template = open(os.path.join(templates_path, 'dialog_choice.json'), 'r').read() \
            .replace('$ID', atom_id).replace('$POSITION', '%s' % str(position))
        return {x.get('id'): Atom(x) for x in json.loads(template)}

    def build(self, scene):
        self.branch_idx = 0
        self.processed_passages = dict()
        self.build_branch(scene, self.starting_passage)

    def build_branch(self, scene, passage):
        existing_branch_id = self.processed_passages.get(passage.get('name'))
        if existing_branch_id:
            return existing_branch_id
        self.branch_idx += 1
        branch_id = '%s#%d' % (ATOM_BRANCH, self.branch_idx)
        self.processed_passages.update({passage.get('name'): branch_id})
        branch_atom = scene.atoms.get(branch_id)
        branch_duration_atom = scene.atoms.get('%s-Duration' % branch_id)
        animation_pattern = branch_atom.storables.get('AnimationPattern')
        existing_triggers = copy.deepcopy(animation_pattern.data['triggers'])
        existing_triggers = {x.get('displayName'): x for x in existing_triggers}
        new_triggers, total_time = self.build_trigger(scene, passage, existing_triggers)
        animation_pattern.data['triggers'] = new_triggers
        branch_duration_atom.storables.get('Step').data['transitionToTime'] = str(total_time)
        return branch_id

    def build_trigger(self, scene, passage, existing_triggers, start_time=DEFAULT_START_TIME):
        triggers = list()
        trigger_name = '%s:%s' % (NAME_PREFIX, passage.get('name'))
        if trigger_name not in existing_triggers:
            trigger = json.load(open(os.path.join(self.templates_path, 'trigger.json'), 'r'))
            trigger['displayName'] = trigger_name
        else:
            trigger = existing_triggers.pop(trigger_name)

        # Strip all dialog actions, but keep others found
        actions = list()
        if start_time == DEFAULT_START_TIME:
            actions += self.get_hide_choices_actions()
        actions += [x for x in trigger.get('startActions') if not x.get('name', '').startswith('%s:' % NAME_PREFIX)]
        trigger['startActions'] = actions

        # Determine flow based on tags
        tags = passage.get('tags', [])
        try:
            target, receiver, duration, prompt = self.parse_tags(tags)
        except Exception:
            raise Exception("Malformed tags in passage '%s'" % passage.get('name'))

        # Figure out start and end times
        end_time = start_time + duration + DEFAULT_MESSAGE_BUFFER
        trigger['startTime'] = str(start_time)
        trigger['endTime'] = str(start_time + DEFAULT_PROMPT_BUFFER) if prompt else str(end_time)

        # Clean message content
        links = self.fix_links(passage.get('links', []))
        content = re.sub(r'\[\[[^\]]+\]\]', '', passage.get('text')).strip()

        # Create actions and add to trigger
        if target and receiver:
            trigger['startActions'] += self.get_bubble_actions(target, receiver, content, duration)

        # Create actions to set dialog buttons
        if len(links) == 0:
            trigger['startActions'] += self.get_restart_actions()
        elif prompt:
            trigger['startActions'] += self.get_prompt_actions()

        # Append trigger to list
        triggers.append(trigger)

        # Follow links to create complete timeline out of triggers
        for link_idx, link in enumerate(links):
            link_id = link.get('link')
            follow_passage = self.passages.get(link_id)
            if prompt:
                branch_id = self.build_branch(scene, follow_passage)
                trigger['startActions'] += self.get_button_actions(link, link_idx, branch_id)
            else:
                # Only follow first link for non-prompting dialogs
                child_triggers, end_time = self.build_trigger(scene, follow_passage, existing_triggers, end_time)
                triggers += child_triggers
                break

        return triggers, end_time

    def get_hide_choices_actions(self):
        actions = list()
        actions.append({
            "name": "%s:%s-Choices:Disable" % (NAME_PREFIX, ATOM_DIALOG),
            "receiverAtom": "%s-Choices" % ATOM_DIALOG,
            "receiver": "AtomControl",
            "receiverTargetName": "on",
            "boolValue": "false"
        })
        return actions

    def get_button_actions(self, link, link_idx, branch_id):
        actions = list()
        receiver_atom = "%s#%d" % (ATOM_CHOICE, link_idx + 1)
        actions.append({
            "name": "%s:%s:ButtonColor" % (NAME_PREFIX, receiver_atom),
            "receiverAtom": receiver_atom,
            "receiver": "ButtonColor",
            "receiverTargetName": "color",
            "color": CHOICE_COLORS[link.get('color')]
        })
        actions.append({
            "name": "%s:%s:Text" % (NAME_PREFIX, receiver_atom),
            "receiverAtom": receiver_atom,
            "receiver": "Text",
            "receiverTargetName": "text",
            "stringValue": link.get('safe_name')
        })
        actions.append({
            "name": "%s:%s:SetBranch" % (NAME_PREFIX, receiver_atom),
            "receiverAtom": receiver_atom,
            "receiver": "plugin#0_JayJayWon.ActionGrouper",
            "receiverTargetName": "act1Atom1Name",
            "stringValue": branch_id
        })
        actions.append({
            "name": "%s:%s:Enable" % (NAME_PREFIX, receiver_atom),
            "receiverAtom": receiver_atom,
            "receiver": "AtomControl",
            "receiverTargetName": "on",
            "boolValue": "true"
        })
        return actions

    def get_restart_actions(self):
        actions = list()
        receiver_atom = "%s-StartBtn" % ATOM_DIALOG
        actions.append({
            "name": "%s:%s:Enable" % (NAME_PREFIX, receiver_atom),
            "receiverAtom": receiver_atom,
            "receiver": "AtomControl",
            "receiverTargetName": "on",
            "boolValue": "true"
        })
        return actions

    def get_prompt_actions(self):
        actions = list()

        # Hide all buttons
        for idx in range(self.choice_count_max):
            receiver_atom = "%s#%d" % (ATOM_CHOICE, idx + 1)
            actions.append({
                "name": "%s:%s:Disable" % (NAME_PREFIX, receiver_atom),
                "receiverAtom": receiver_atom,
                "receiver": "AtomControl",
                "receiverTargetName": "on",
                "boolValue": "false"
            })

        # Show dialog choices
        actions.append({
            "name": "%s:%s-Choices:Enable" % (NAME_PREFIX, ATOM_DIALOG),
            "receiverAtom": "%s-Choices" % ATOM_DIALOG,
            "receiver": "AtomControl",
            "receiverTargetName": "on",
            "boolValue": "true"
        })

        return actions

    def get_bubble_actions(self, target, receiver, content, duration=DEFAULT_DURATION):
        actions = list()
        actions.append({
            "name": "%s:%s:%s:Lifetime" % (NAME_PREFIX, target, receiver),
            "receiverAtom": target,
            "receiver": receiver,
            "receiverTargetName": "bubbleLifetime",
            "floatValue": str(duration)
        })
        actions.append({
            "name": "%s:%s:%s:Text" % (NAME_PREFIX, target, receiver),
            "receiverAtom": target,
            "receiver": receiver,
            "receiverTargetName": "bubbleText",
            "stringValue": content
        })
        return actions

    def get_atom_counts(self, passage=None):
        branch_count = 0
        choice_count = 0
        if not passage:
            self.processed_passages = dict()
            passage = self.starting_passage
            branch_count += 1
        elif passage.get('name') in self.processed_passages.keys():
            return 0, 0

        self.processed_passages.update({passage.get('name'): ''})
        tags = passage.get('tags', [])
        links = self.fix_links(passage.get('links', []))

        try:
            target, receiver, duration, prompt = self.parse_tags(tags)
        except Exception:
            raise Exception("Malformed tags in passage '%s'" % passage.get('name'))

        if prompt and len(links) > choice_count:
            choice_count = len(links)

        for link in links:
            if prompt:
                branch_count += 1
            atom_counts = self.get_atom_counts(self.passages.get(link.get('link')))
            branch_count += atom_counts[0]
            if atom_counts[1] > choice_count:
                choice_count = atom_counts[1]

        self.branch_count_max = branch_count
        self.choice_count_max = choice_count
        return branch_count, choice_count

    def fix_links(self, links):
        for link in links:
            link['link'] = link.get('link').split('|')[-1].split('<-')[0]
            link['name'] = link.get('name').split('|')[0].split('<-')[-1]
            link['safe_name'] = link.get('name')
            link['color'] = CHOICE_COLOR
            for color_name, color in CHOICE_COLORS.items():
                if link.get('name').startswith('%s:' % color_name):
                    link['safe_name'] = link.get('name')[len(color_name) + 1:]
                    link['color'] = color_name.upper()
                    break
        return links

    def parse_tags(self, tags):
        target = ''
        receiver = ''
        duration = DEFAULT_DURATION
        prompt = tags[-1] == 'prompt'
        if tags[0].lower() == 'delay':
            if len(tags) > 1:
                duration = float(tags[1])
        else:
            if len(tags) == 1:
                raise Exception()
            target = tags[0]
            if tags[1].lower() not in ['says', 'thinks']:
                raise Exception()
            receiver = "SpeechBubble" if tags[1].lower() == 'says' else "ThoughtBubble"
            if len(tags) > 2 and not prompt:
                duration = float(tags[2])
        return target, receiver, duration, prompt
