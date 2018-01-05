#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

# import sys
# sys.path.append('vendor')
# from pprint_utf import pprint

# Regex
ALL_EN = re.compile(u'^[a-zA-Z0-9\\s]+$')
ALL_CN = re.compile(u'^[\u4e00-\u9fa5]+$')
CN_EN  = re.compile(u'^[\u4e00-\u9fa5\\s]+[^\u4e00-\u9fa5]+$')
CN_SPACE_EN = re.compile(u'^[\u4e00-\u9fa5\\s]+\\s[^\u4e00-\u9fa5]+$')

# Mappings
TYPOS = {u'高薪': u'高新'}

ABBRES = {
    'Blvd': 'Boulevard',
    'Rd': 'Road',
    'Lu': 'Road',
    'Rd(E)': 'East Road',
    'Rd(W)': 'West Road',
    'Rd(N)': 'North Road',
    'Rd(S)': 'South Road',
    'Expy': 'Expressway',
    'Str': 'Street',
    'St': 'Street',
    'Jie': 'Street',
    u'Jie（S.）': 'Street',
    'Qu': 'District',
}


def get_zh_tag(tags):
    return next((t for t in tags 
                   if  t['type'] == 'name' 
                   and t['key']  == 'zh'), 
                 None)

def audit_tags(tags):
    # Apply what we learnt in audit.ipynb:
    for i, tag in enumerate(tags):
        value = tag['value']

        # Fix name tags
        if tag['key'] == 'name' and (ALL_EN.match(value) or 
                                     CN_EN.match(value)):
            # Use name:zh as the gold standard
            zh_tag = get_zh_tag(tags)            
            if zh_tag and ALL_CN.match(zh_tag['value']):
                tags[i]['value'] = zh_tag['value']

            # Fix tags with a space separating the Chinese 
            # and English parts, such as:
            # '兵马俑 terracotta army'
            # '高薪四路 / Gaoxin Si Lu'
            elif CN_SPACE_EN.match(value):
                cn, _, _ = value.partition(' ')
                tags[i]['value'] = cn

            # Fix typos
            # '高薪' => '高新'
            for wrong, right in TYPOS.items():
                if wrong in value:
                    tags[i]['value'] = tags[i]['value'].replace(wrong, right)

        # Fix abbrevations in name:en
        if tag['key'] == 'en':
            for abbre, full in ABBRES.items():
                if value.endswith(abbre):
                    tags[i]['value'] = tags[i]['value'].replace(abbre, full)

    return tags
