import os
import json

from app.project import Project

import logging
logging.basicConfig(
    filename='output.log',
    filemode='a',
    format='%(process)d - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

config = json.load(open('config.json', 'r'))
VAM_PATH = config.get('VAM_PATH')
SCENES_PATH = os.path.join(VAM_PATH, 'Saves', 'scene')
PROJECTS_PATH = config.get('PROJECTS_PATH', os.path.join('.', 'projects'))
TEMPLATES_PATH = config.get('TEMPLATES_PATH', os.path.join('.', 'templates'))

try:
    if not os.path.isdir(VAM_PATH):
        raise FileNotFoundError("VAM_PATH not set or does not exist!  Please specify in config.json.")
    if not os.path.isdir(PROJECTS_PATH):
        raise FileNotFoundError("Could not find PROJECTS_PATH! Are you sure it exists?")
    if not os.path.isdir(TEMPLATES_PATH):
        raise FileNotFoundError("Could not find TEMPLATES_PATH! Are you sure it exists?")

    for project_name in os.listdir(PROJECTS_PATH):
        project = Project(
            name=project_name,
            projects_path=PROJECTS_PATH,
            templates_path=TEMPLATES_PATH,
            scenes_path=SCENES_PATH
        )
        project.scaffold()
except Exception as e:
    logging.exception(e)
