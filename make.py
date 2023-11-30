# Use genson to generate a schema from one or more JSON files.
# Use Microsoft's jschema-to-python to generate a Python class from the schema.

import os
import sys
import json
from genson import SchemaBuilder
import subprocess
from pathlib import Path
import re
import logging

SCRIPT_DIR = Path(__file__).parent
INPUT_DIR = SCRIPT_DIR / 'input'
OUTPUT_DIR = SCRIPT_DIR / 'output'

def sanitize_input(input_str):
    # Replace invalid characters with underscores
    return re.sub(r'[^A-Za-z0-9_]', '_', input_str)

def ensure_proper_py_names(input_str):
    # Prepend an underscore if the string starts with a number
    if re.match(r'^[0-9]', input_str):
        input_str = '_' + input_str

    # Replace invalid characters with underscores
    input_str = sanitize_input(input_str)

    # Prevent starting with an underscore
    if input_str.startswith('_'):
        input_str = 'x' + input_str
    return input_str

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('make')

    if not INPUT_DIR.exists():
        logger.error(f'Input directory does not exist: {INPUT_DIR}')
        return
    
    if not OUTPUT_DIR.exists():
        logger.info(f'Creating output directory: {OUTPUT_DIR}')
        OUTPUT_DIR.mkdir()
    
    if not any(INPUT_DIR.glob('*.json')):
        logger.error(f'No JSON files found in input directory: {INPUT_DIR}')
        return
    
    root_class_name = input('Please enter a name for root class: ')
    root_class_name = sanitize_input(root_class_name)
    module_name = input('Please enter a name for Python module: ')
    module_name = sanitize_input(module_name)

    PY_DIR = OUTPUT_DIR / module_name.lower()

    if PY_DIR.exists():
        logger.info(f'Deleting existing output directory: {PY_DIR}')
        for file in PY_DIR.glob('*'):
            os.remove(file)
        os.rmdir(PY_DIR)

    logger.info('Reading JSON files...')
    builder = SchemaBuilder()
    for file in INPUT_DIR.glob('*.json'):
        logger.info(f'Reading {file.name}...')
        with open(file) as f:
            j = None
            try:
                j = json.load(f)
            except json.decoder.JSONDecodeError:
                print(f'Error reading {file.name}. Skipping.')
                continue

            if not isinstance(j, dict):
                print(f'Error reading {file.name}. Skipping.')
                continue

            try:
                builder.add_object(j)
            except TypeError:
                print(f'Error reading {file.name}. Skipping.')
                continue

    # No exception handling after here, because I want to crash if the schema is invalid.
    JSON_SCHEMA = builder.to_schema()
    JSON_SCHEMA['title'] = root_class_name

    logger.info(f'Writing schema to {OUTPUT_DIR}')
    schema_file = OUTPUT_DIR / f'{root_class_name.lower()}.json'
    with open(schema_file, 'w') as f:
        f.write(json.dumps(JSON_SCHEMA, indent=2))

    logger.info(f'Generating Python class to {PY_DIR}')
    subprocess.run([
        sys.executable,
        '-m',
        'jschema_to_python',
        '-s',
        str(schema_file),
        '-o',
        str(PY_DIR),
        '-r',
        root_class_name,
        '-m',
        module_name,
    ], check=True)

    logger.info('Cleaning up...')
    print('Done.')


if __name__ == '__main__':
    main()