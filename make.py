# Use genson to generate a schema from one or more JSON files.
# Use Microsoft's jschema-to-python to generate a Python class from the schema.

import os
import sys
import json
from genson import SchemaBuilder
import subprocess
from pathlib import Path

# Path to the directory containing this script.
SCRIPT_DIR = Path(__file__).parent

# Path to the directory containing the JSON files.
INPUT_DIR = SCRIPT_DIR / 'input'

# Path to the directory containing the generated Schema.
SCHEMA_DIR = SCRIPT_DIR / 'schema'

# Path to the directory containing output files.
OUTPUT_DIR = SCRIPT_DIR / 'output'

def main():
    # Check that the input directory exists.
    if not INPUT_DIR.exists():
        print(f'Input directory does not exist: {INPUT_DIR}')
        return
    
    # Create the output directory if it doesn't exist.
    if not OUTPUT_DIR.exists():
        print(f'Creating output directory: {OUTPUT_DIR}')
        OUTPUT_DIR.mkdir()
    
    # Check if there are any JSON files in the input directory.
    if not any(INPUT_DIR.glob('*.json')):
        print(f'No JSON files found in input directory: {INPUT_DIR}')
        return
    
    # Get name for class at root of object model.
    root_class_name = input('Enter name for root class: ')

    PY_DIR = OUTPUT_DIR / root_class_name.lower()

    # Delete the output directory if it exists.
    if PY_DIR.exists():
        print(f'Deleting existing output directory: {PY_DIR}')
        for file in PY_DIR.glob('*'):
            os.remove(file)
        os.rmdir(PY_DIR)

    # Create a schema from the JSON files.
    print('Reading JSON files...')
    builder = SchemaBuilder()
    for file in INPUT_DIR.glob('*.json'):
        print(f'Reading {file.name}...')
        with open(file) as f:
            builder.add_object(json.load(f))

    # Add the root class name to the schema.
    JSON_SCHEMA = builder.to_schema()
    JSON_SCHEMA['title'] = root_class_name

    print('\nGenerating schema...')
    # Write the schema to a file.
    schema_file = OUTPUT_DIR / f'{root_class_name.lower()}.json'
    with open(schema_file, 'w') as f:
        f.write(json.dumps(JSON_SCHEMA, indent=2))


    print('\nGenerating Python class...')
    # Generate a Python class from the schema.
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
        '-v'
    ], check=True)

    # Re-write the JSON schema, because jschema_to_python deletes it.
    with open(schema_file, 'w') as f:
        f.write(builder.to_json(indent=2))

    
    print('\nDone.')


if __name__ == '__main__':
    main()