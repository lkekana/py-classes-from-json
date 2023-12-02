# Use genson to generate a schema from one or more JSON files.
# Use Microsoft's jschema-to-python to generate a Python class from the schema.

import os
import sys
import json
from genson import SchemaBuilder
from jschema_to_python_2.object_model_module_generator import ObjectModelModuleGenerator
import subprocess
from pathlib import Path
import re
import logging
import argparse

SCRIPT_DIR = Path(__file__).parent
INPUT_DIR = SCRIPT_DIR / 'input'
OUTPUT_DIR = SCRIPT_DIR / 'output'

# key = class name, value = schema
sub_definitions = {}

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


def collect_and_reorder_inner_objects(schema):
    if not isinstance(schema, dict):
        return schema
    
    objects_to_reorder = []

    # if we were passed an object
    if schema.get('properties') is not None:
        for key, value in schema.get('properties', {}).items():
            if value.get('type') == 'object':
                schema['properties'][key] = collect_and_reorder_inner_objects(value)
                sub_definitions[key] = value
                objects_to_reorder.append(key)
            elif value.get('type') == 'array':
                schema['properties'][key] = collect_and_reorder_inner_objects(value)

        for key in objects_to_reorder:
            schema['properties'][key] = {'$ref': f'#/$defs/{key}'}

    # if we were passed an array
    elif schema.get('items') is not None:
        for key, value in schema.get('items', {}).items():
            # check if value is a dict
            if isinstance(value, dict) and value.get('type') == 'object':
                schema['items'][key] = collect_and_reorder_inner_objects(value)
                sub_definitions[key] = value
                objects_to_reorder.append(key)

        for key in objects_to_reorder:
            schema['items'][key] = {'$ref': f'#/$defs/{key}'}

    return schema

    

# input json schema (dict), output json schema (dict) with definitions placed at the end
def refactor_inner_classes(schema):
    collect_and_reorder_inner_objects(schema)
    schema['$defs'] = {}
    for key, value in sub_definitions.items():
        schema['$defs'][key] = value
    sub_definitions.clear()
    return schema


def main():
    logging.basicConfig(level=logging.WARNING)
    logger = logging.getLogger('make')

    parser = argparse.ArgumentParser(description="Generate a JSON schema and Python class from one or more JSON files.")
    parser.add_argument("--input-dir", help="Path to input directory", default="input/")
    parser.add_argument("--output-dir", help="Path to output directory", default="output/")
    parser.add_argument("--root-class-name", help="Name of root class / parent object")
    parser.add_argument("--module-name", help="Name of Python module")
    parser.add_argument("-v", "--verbose", help="Increase output verbosity", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        # print as much as possible
        logger.setLevel(logging.DEBUG)
        logging.getLogger('genson').setLevel(logging.DEBUG)
        logging.getLogger('jschema_to_python').setLevel(logging.DEBUG)

    if args.input_dir:
        INPUT_DIR = Path(args.input_dir)

    if args.output_dir:
        OUTPUT_DIR = Path(args.output_dir)        

    if not INPUT_DIR.exists():
        logger.error(f'Input directory does not exist: {INPUT_DIR}')
        return
    
    if not OUTPUT_DIR.exists():
        logger.info(f'Creating output directory: {OUTPUT_DIR}')
        OUTPUT_DIR.mkdir()
    
    if not any(INPUT_DIR.glob('*.json')):
        logger.error(f'No JSON files found in input directory: {INPUT_DIR}')
        return
    
    root_class_name = None
    if not args.root_class_name:
        root_class_name = input('Please enter a name for root class: ')
    else:
        root_class_name = ensure_proper_py_names(args.root_class_name)
    root_class_name = sanitize_input(root_class_name)

    module_name = None
    if not args.module_name:
        module_name = input('Please enter a name for Python module: ')
    else:
        module_name = ensure_proper_py_names(args.module_name)
    module_name = sanitize_input(module_name)
    module_name = module_name.lower()

    PY_DIR = OUTPUT_DIR / module_name

    if PY_DIR.exists():
        logger.info(f'Deleting existing output directory: {PY_DIR}')
        for file in PY_DIR.glob('*'):
            os.remove(file)
        os.rmdir(PY_DIR)

    logger.info('Reading JSON files...')
    builder = SchemaBuilder()
    # for each json in INPUT_DIR that does not end with -schema.json
    for file in INPUT_DIR.glob('*.json'):
        logger.info(f'Checking {file.name}...')
        if file.name.endswith('-schema.json'):
            logger.info(f'Skipping {file.name}...')
            continue

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
    JSON_SCHEMA = refactor_inner_classes(JSON_SCHEMA)

    logger.info(f'Writing schema to {OUTPUT_DIR}')
    schema_file = OUTPUT_DIR / f'{root_class_name.lower()}-schema.json'
    with open(schema_file, 'w') as f:
        f.write(json.dumps(JSON_SCHEMA, indent=2))

    logger.info(f'Generating Python class to {PY_DIR}')
    '''
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
    '''

    # make an object resembling args for ObjectModelModuleGenerator to consume
    class Args:
        def __init__(self):
            self.output_directory = str(PY_DIR)
            self.force = True
            self.module_name = module_name
            self.schema_path = str(schema_file)
            self.hints_file_path = None
            self.root_class_name = root_class_name

    # make an instance of Args
    args = Args()

    # make an instance of ObjectModelModuleGenerator
    generator = ObjectModelModuleGenerator(args)
    generator.generate()

    logger.info('Cleaning up...')
    print('Done.')


if __name__ == '__main__':
    main()