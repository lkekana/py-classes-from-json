# py-classes-from-json
Generate Python classes using one or more JSON strings.
Uses both genson and Microsoft's jschema-to-python to achieve this.

## Installation
```bash
git clone (this repo)
pip install -r requirements.txt
```

## Usage
```
usage: python make.py [-h] [--input-dir INPUT_DIR] [--output-dir OUTPUT_DIR]
               [--root-class-name ROOT_CLASS_NAME] [--module-name MODULE_NAME]
               [-v]

Generate a JSON schema and Python class from one or more JSON files.

optional arguments:
  -h, --help            show this help message and exit
  --input-dir INPUT_DIR
                        Path to input directory
  --output-dir OUTPUT_DIR
                        Path to output directory
  --root-class-name ROOT_CLASS_NAME
                        Name of root class / parent object
  --module-name MODULE_NAME
                        Name of Python module
  -v, --verbose         Increase output verbosity
  ```

## Example
```bash
python make.py --input-dir ./examples --output-dir ./examples --root-class-name JobEvent --module-name myEvents
```

You can also test the generated classes by running the following (in the examples folder)
```bash
python test.py
```

## Thanks to
- Jon Wolverton & contributors (https://pypi.org/project/genson/)
- The contributors at Microsoft (https://github.com/microsoft/jschema-to-python)