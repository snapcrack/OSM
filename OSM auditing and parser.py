######PRELIMINARY NECESSITIES##########

import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

import cerberus

import schema

philly = "sample.osm" 

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

#####################################################################CRUNCHING THE FILE#######################################################

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET  # Use cElementTree or lxml if too slow

OSM_FILE = "sample.osm"
SAMPLE_FILE = "sample.osm"

k = 10 # Parameter: take every k-th top level element

def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag

    Reference:
    http://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
    """
    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


with open(SAMPLE_FILE, 'wb') as output:
    output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    output.write('<osm>\n  ')

    # Write every kth top level element
    for i, element in enumerate(get_element(OSM_FILE)):
        if i % k == 0:
            output.write(ET.tostring(element, encoding='utf-8'))
    output.write('</osm>')


#######################################################################COUNTING XML TAGS############################################################
def count_tags(filename):
    tags = {}
    for i, element in enumerate(get_element(filename)):
        if element.tag not in tags.keys():
            tags[element.tag] = 1
        else:
            tags[element.tag] += 1
    return tags


####EXECUTE FUNCTION

count_tags(philly)

#########################################################COUNTING KEYS####################################################################

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

def key_type(element, keys):
    if element.tag == "tag":
        for tag in element.iter("tag"):
            if lower.search(tag.attrib['k']):
               keys['lower'] += 1
            elif lower_colon.search(tag.attrib['k']):
               keys['lower_colon'] += 1
            elif problemchars.search(tag.attrib['k']):
               keys['problemchars'] += 1
            elif street_type_re.search(tag.attrib['k']):
                keys['street_type'] +=1
            else:
               keys['other'] += 1
    return keys

def process_map(filename):
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0, "street_type": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)

    return keys

#####EXECUTE FUNCTION

keys = process_map(philly)
pprint.pprint(keys)


#################################################################AUDIT FUNCTIONS################################################################################
from collections import defaultdict

expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons"]

#function to fix memory issues in auditing the full OSM file
def get_element(osm_file, tags=('node', 'way')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

#postcode stuff
def is_postcode(elem):
    return (elem.attrib['k'] == "addr:postcode")

def audit_postcode(postcodes, postcode):
    p = re.match(r'^\d{5}$', postcode)
    #postcodes = defaultdict(set)
    if p:
        return postcode
    else:
        postcodes[postcode].add(postcode)
        
#audit

def audit(osmfile):
    street_types = defaultdict(set)
    ### the 'postcodes' dictionary is created only once here:
    postcodes = defaultdict(set)
    # loop over every element in the file 'osm_file'
    ### use 'get_element()' here (instead of '.iterparse()':
    for elem in get_element(osmfile):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
                elif is_postcode(tag):
                    audit_postcode(postcodes, tag.attrib['v'])
    #osm_file.close()
    return street_types, postcodes


####EXECUTE FUNCTION
audit(philly)


#########################################################CLEANING FUNCTIONS################################################################

#cleaning dirty street names in our audit
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Pike", "Way"]

mapping = { "St": "Street",
            "St.": "Street",
            "st": "Street",
            "st.": "Street",
            "Dr.": "Drive",
            "Rd": "Road",
            "avenue": "Avenue",
            "road": "Road",
            "street": "Street",
            "way": "Way",
            "Blvd.": "Boulevard",
            "Rd.": "Road",
            "Ave": "Avenue",
            }

def update_name(name, mapping):
    m = street_type_re.search(name)
    if m:
        if m.group() in mapping.keys():
            name = re.sub(m.group(), mapping[m.group()], name)
    return name

'''UPDATED POSTCODE-CLEANING FUNCTION IS HERE WITH ADDITIONAL REGEX TO FIX EXTANEOUS FOUR-DIGITS IN POSTCODES'''
def update_postcode(postcode):
    clean_postcode = re.findall(r'^[A-Z]{2} (\d{5})$', postcode)
    clean_postcode2 = re.findall(r'(\d{5}).\d{4}$', postcode)
    if clean_postcode:
        cleaned_postcode = clean_postcode[0]
        return cleaned_postcode
    elif clean_postcode2:
        cleaned_postcode = clean_postcode2[0]
        return cleaned_postcode
    else:
        return postcode


 ####################################################################THE REALLY BIG ONE############################################################

 OSM_PATH = SAMPLE_FILE

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

#SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    #way_tag = {}
    tags = []  # Handle secondary tags the same way for both node and way elements
    #node_tag = {}
    id_list = []

    if element.tag == 'node':
        for attrib in element.attrib:
            if attrib in NODE_FIELDS:
                node_attribs[attrib] = element.attrib[attrib]
        for child in element:
            node_tag = {}
            if PROBLEMCHARS.match(child.attrib["k"]):
                continue
            elif LOWER_COLON.match(child.attrib["k"]):
                node_tag["type"] = child.attrib["k"].split(":",2)[0]
                node_tag["key"] = child.attrib["k"].split(":",2)[1]
                node_tag["id"] = element.attrib["id"]
                if child.attrib['k'] == 'addr:postcode':
                    node_tag["value"] = update_postcode(child.attrib["v"])
                    tags.append(node_tag)
                elif child.attrib['k'] == 'addr:street':
                    node_tag["value"] = update_name(child.attrib["v"], mapping)
                    tags.append(node_tag)
                # otherwise, don't clean:
                else:
                    node_tag["type"] = "regular"
                    node_tag["key"] = child.attrib["k"]
                    node_tag["id"] = element.attrib["id"]
                    node_tag["value"] = child.attrib["v"]
                    tags.append(node_tag)
    elif element.tag == 'way':
        for attrib in element.attrib:
            if attrib in WAY_FIELDS:
                way_attribs[attrib] = element.attrib[attrib]
        for child in element:
            way_node = {}
            way_tag = {}
            if child.tag == "nd":
                if element.attrib["id"] not in id_list:
                    i=0
                    id_list.append(element.attrib["id"])
                    way_node["id"] = element.attrib["id"]
                    way_node["node_id"] = child.attrib["ref"]
                    way_node["position"] = i
                    #print way_node
                    way_nodes.append(way_node.copy())
                else:
                    i=i+1
                    way_node["id"] = element.attrib["id"]
                    way_node["node_id"] = child.attrib["ref"]
                    way_node["position"] = i
                    way_nodes.append(way_node.copy())
            if child.tag == "tag":
                if PROBLEMCHARS.match(child.attrib["k"]):
                    continue
                elif LOWER_COLON.match(child.attrib["k"]):
                    way_tag["type"] = child.attrib["k"].split(":",2)[0]
                    way_tag["key"] = child.attrib["k"].split(":",2)[1]
                    way_tag["id"] = element.attrib["id"]
                # if the 'k' attribute is 'addr:postcode':
                    if child.attrib['k'] == 'addr:postcode':
                        way_tag["value"] = update_postcode(child.attrib["v"])
                        tags.append(way_tag)
                # or if the 'k' attribute is 'addr:street':
                    elif child.attrib['k'] == 'addr:street':
                        way_tag["value"] = update_name(child.attrib["v"], mapping)
                        tags.append(way_tag)
                # otherwise, don't clean:
                else:
                    way_tag["type"] = "regular"
                    way_tag["key"] = child.attrib["k"]
                    way_tag["id"] = element.attrib["id"]
                    way_tag["value"] = child.attrib["v"]
                    tags.append(way_tag)
    if element.tag == 'node':
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


###############################################################BIG ONE, PART 2####################################################################

def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
        codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])
'''

if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=True)
'''

#####EXECUTE FUNCTIONS

shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular')

process_map(philly, validate=False)