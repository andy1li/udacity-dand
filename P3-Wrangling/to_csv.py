#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import codecs
import lxml.etree as ET
import re

from audit import audit_tags

#import cerberus
#import schema
#SCHEMA = schema.schema

# PATHS
OSM_FILE    = 'osm/Xian-Xianyang.osm'
SAMPLE_FILE = 'osm/sample.osm'

NODES_PATH     = "csv/nodes.csv"
NODE_TAGS_PATH = "csv/nodes_tags.csv"

WAYS_PATH      = "csv/ways.csv"
WAY_TAGS_PATH  = "csv/ways_tags.csv"
WAY_NODES_PATH = "csv/ways_nodes.csv"

RELATIONS_PATH          = "csv/relations.csv"
RELATION_TAGS_PATH      = "csv/relations_tags.csv"
RELATION_NODES_PATH     = "csv/relations_nodes.csv"
RELATION_WAYS_PATH      = "csv/relations_ways.csv"
RELATION_RELATIONS_PATH = "csv/relations_relations.csv"

# FILEDS
NODE_FIELDS      = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']

WAY_FIELDS       = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS  = NODE_TAGS_FIELDS
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

RELATION_FIELDS           = WAY_FIELDS
RELATION_TAGS_FIELDS      = NODE_TAGS_FIELDS
RELATION_NODES_FIELDS     = ['id', 'node_id', 'position', 'role']
RELATION_WAYS_FIELDS      = ['id', 'way_id', 'position', 'role']
RELATION_RELATIONS_FIELDS = ['id', 'relation_id', 'position', 'role']

# REGEXES
LOWER_COLON  = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

def shape_tag(el, t):         
    tag = {
        'id'   : el.attrib['id'],
        'key'  : t.attrib['k'],
        'value': t.attrib['v'],
        'type' : 'regular'
    }
    
    if LOWER_COLON.match(tag['key']):
        tag['type'], _, tag['key'] = tag['key'].partition(':')
        
    return tag
    
def shape_way_node(el, i, nd):
    return {
        'id'       : el.attrib['id'],
        'node_id'  : nd.attrib['ref'],
        'position' : i
    }

def shape_relation_node(el, i, member):
    return {
        'id'                       : el.attrib['id'],
        member.attrib['type']+'_id': member.attrib['ref'],
        'position'                 : i,
        'role'                     : member.attrib['role']
    }

def get_relation_members(el, type):
    return [shape_relation_node(el, i, member) 
            for i, member 
            in enumerate(el.iter('member'))
            if member.attrib['type'] == type]


def shape_element(el, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS):
    """Clean and shape node, way or relation XML element to Python dict"""
    tags = [shape_tag(el, t) for t in el.iter('tag')]
    tags = audit_tags(tags) # imported from audit.py
    
    if el.tag == 'node':
        node_attribs = {f: el.attrib[f] for f in node_attr_fields}
        
        return {'node': node_attribs, 'node_tags': tags}
        
    elif el.tag == 'way':
        way_attribs = {f: el.attrib[f] for f in way_attr_fields}
        
        way_nodes = [shape_way_node(el, i, nd) 
                     for i, nd 
                     in enumerate(el.iter('nd'))]
   
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}

    elif el.tag == 'relation':
        relation_attribs = {f: el.attrib[f] for f in way_attr_fields}

        return {
            'relation'          : relation_attribs, 
            'relation_tags'     : tags,
            'relation_nodes'    : get_relation_members(el, 'node'),
            'relation_ways'     : get_relation_members(el, 'way'),
            'relation_relations': get_relation_members(el, 'relation')
        }

# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

# def validate_element(element, validator, schema=SCHEMA):
#     """Raise ValidationError if element does not match schema"""
#     if validator.validate(element, schema) is not True:
#         field, errors = next(validator.errors.iteritems())
#         message_string = "\nElement of type '{0}' has the following errors:\n{1}"
#         error_string = pprint.pformat(errors)
        
#         raise Exception(message_string.format(field, error_string))

class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) 
            for k, v in row.iteritems()
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
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(RELATIONS_PATH, 'w') as relations_file, \
         codecs.open(RELATION_TAGS_PATH, 'w') as relation_tags_file, \
         codecs.open(RELATION_NODES_PATH, 'w') as relation_nodes_file, \
         codecs.open(RELATION_WAYS_PATH, 'w') as relation_ways_file, \
         codecs.open(RELATION_RELATIONS_PATH, 'w') as relation_relations_file:

        nodes_writer     = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)

        ways_writer      = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_tags_writer  = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)

        relations_writer = UnicodeDictWriter(relations_file, RELATION_FIELDS)
        relation_tags_writer  = UnicodeDictWriter(relation_tags_file, RELATION_TAGS_FIELDS)
        relation_nodes_writer = UnicodeDictWriter(relation_nodes_file, RELATION_NODES_FIELDS)
        relation_ways_writer  = UnicodeDictWriter(relation_ways_file, RELATION_WAYS_FIELDS)
        relation_relations_writer = UnicodeDictWriter(relation_relations_file, RELATION_RELATIONS_FIELDS)
        
        nodes_writer.writeheader()
        node_tags_writer.writeheader()

        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        relations_writer.writeheader()
        relation_tags_writer.writeheader()
        relation_nodes_writer.writeheader()
        relation_ways_writer.writeheader()
        relation_relations_writer.writeheader()

        # validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way', 'relation')):
            el = shape_element(element)

            # if validate is True:
            #     validate_element(el, validator)

            if element.tag == 'node':
                nodes_writer.writerow(el['node'])
                node_tags_writer.writerows(el['node_tags'])

            elif element.tag == 'way':
                ways_writer.writerow(el['way'])
                way_tags_writer.writerows(el['way_tags'])
                way_nodes_writer.writerows(el['way_nodes'])
                
            elif element.tag == 'relation':
                relations_writer.writerow(el['relation'])
                relation_tags_writer.writerows(el['relation_tags'])
                relation_nodes_writer.writerows(el['relation_nodes'])
                relation_ways_writer.writerows(el['relation_ways'])
                relation_relations_writer.writerows(el['relation_relations'])

if __name__ == '__main__':
    process_map(OSM_FILE, validate=False)
