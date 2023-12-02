import os
import shutil
import sys
import jsonpickle


def capitalize_first_letter(identifier):
    return identifier[0].capitalize() + identifier[1:]


def create_directory(directory, force):
    if os.path.exists(directory):
        if force:
            shutil.rmtree(directory, ignore_errors=True)
        else:
            exit_with_error("output directory {} already exists", directory)

    os.makedirs(directory)


def to_underscore_separated_name(name):
    result = ""
    first_char = True
    for ch in name:
        if ch.islower():
            next_char = ch
        else:
            next_char = ch.lower()
            if not first_char:
                next_char = "_" + next_char
        first_char = False

        result += next_char
    return result


def class_name_to_private_module_name(class_name):
    # The leading underscore indicates that users are not intended to import
    # the class module individually.
    return "_" + to_underscore_separated_name(class_name)


def unpickle_file(path):
    with open(path, mode="rt") as file_obj:
        contents = file_obj.read()
        return jsonpickle.decode(contents)


def exit_with_error(message, *args):
    sys.stderr.write("error : " + message.format(*args) + "\n")
    sys.exit(1)

# Add the name of a generated class to a JSON file that lists all generated
def add_generated_class(class_name, output_directory):
    generated_classes_path = os.path.join(output_directory, "generated_classes.json")
    if os.path.exists(generated_classes_path):
        generated_classes = unpickle_file(generated_classes_path)
    else:
        generated_classes = []

    generated_classes.append(class_name)

    with open(generated_classes_path, mode="wt") as file_obj:
        file_obj.write(jsonpickle.encode(generated_classes, indent=4))

def get_generated_classes(output_directory):
    generated_classes_path = os.path.join(output_directory, "generated_classes.json")
    if os.path.exists(generated_classes_path):
        return unpickle_file(generated_classes_path)
    else:
        return []

# make frequency table for all items in JSON schema (with type "object") | recursively
def make_frequency_table(schema_object, frequency_table=None):
    if frequency_table is None:
        frequency_table = {}

    if "type" in schema_object and schema_object["type"] and schema_object["type"] == "object":
        for key in schema_object.get("properties", {}):
            if key not in frequency_table:
                frequency_table[key] = 1
            else:
                frequency_table[key] += 1
            make_frequency_table(schema_object["properties"][key], frequency_table)
    elif "type" in schema_object and schema_object["type"] and schema_object["type"] == "array":
        make_frequency_table(schema_object.get("items", {}), frequency_table)
    elif "$ref" in schema_object and schema_object["$ref"]:
        if schema_object["$ref"] not in frequency_table:
            frequency_table[schema_object["$ref"]] = 1
        else:
            frequency_table[schema_object["$ref"]] += 1

    return frequency_table