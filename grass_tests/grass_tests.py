#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat Jul  6 23:00:17 2019

@author: lucadelu
"""
import os
import sys
from subprocess import PIPE
from collections import OrderedDict
from time import sleep
from datetime import date
from copy import deepcopy
import json
from grass.pygrass.modules.shortcuts import vector as v
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import display as d
from grass.exceptions import CalledModuleError
from osgeo import ogr
GML = ogr.GetDriverByName('GML')
GEOJSON = ogr.GetDriverByName('GeoJSON')
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
#DIR_PATH = '/home/lucadelu/github/caniuse/grass_tests/'

def ori_info(path, driver):
    dataSource = driver.Open(os.path.join(DIR_PATH, path))
    output = {}
    if dataSource is None:
        print('Could not open {}'.format(path))
        return False
    else:
        for layer in dataSource:
            count = layer.GetFeatureCount()
            name = layer.GetName()
            output[name] = count
    return output

def run_test(path, out, outputype):
    """Run a single test
    
    :param str path: path to input file
    :param str out: the output file name, usually the test name
    :param str outputype: the required output type
    """
    print("#################### {} ####################\n".format(out))
    if path.startswith('http'):
        try:
            v.in_ogr(input=path, output=out, flags='o', overwrite=True,
                      gdal_doo='GML_ATTRIBUTES_TO_OGR_FIELDS=YES', quiet=True)
        except CalledModuleError:
            return False, "WFS not working"
    else:
        try:
            v.in_ogr(input=os.path.join(DIR_PATH, path), output=out,
                      flags='o', gdal_doo='GML_ATTRIBUTES_TO_OGR_FIELDS=YES',
                      overwrite=True, quiet=True)
        except CalledModuleError:
            return False, "Error linking vector"
    try:
        exists = g.list(type='vector', pattern=out)
    except CalledModuleError:
            return False, "Error linking vector"
    print(exists)
    if not exists:
        return False, "Error linking vector"
    vinfo = v.info(flags='t', map=out, stdout_=PIPE).outputs.stdout
    outinfo = dict(item.split("=") for item in vinfo.splitlines())
    print(outinfo)
    if '3d' in out:
        if int(outinfo['map3d']) == 1:
            return True, ''
        else:
            return False, 'Vector imported but not 3D'
    if outputype == 'display':
        g.region(vector=out)
        d.mon(start='png', output=os.path.join(DIR_PATH, "{}.png".format(out)),
              overwrite=True)
        sleep(5)
        d.vect(out)
        sleep(5)
        d.mon(stop='png')
    #elif outputype == 'edit':
    #elif outputype == 'create':           
    return True, ''

def all_tests(formatt, tests):
    output = OrderedDict((('software', 'GRASS GIS'), ('version', ver_dict['version'])))
    if formatt == 'gml':
        driver = GML
    elif formatt == 'geojson':
        driver = GEOJSON
    else:
        print("Not supported format")
        return False
    output['results'] = {formatt: OrderedDict()}
    for key, vals in tests.items():
        outtest = OrderedDict([["result", "Non supported"], ["notes", "None"],
                               ["dataUsed", ''], ["dateOfTest", today]])
        if vals['data'] is None:
            outtest.update({'result': 'No tested'})
            output['results'][formatt][key] = deepcopy(outtest)
            continue
        ininfo = ori_info(vals['data'], driver)
        print(ininfo)
        outrun = run_test(vals['data'], key, vals['check'])
        infile = os.path.split(vals['data'])[-1]
        usedfile = "https://raw.githubusercontent.com/INSPIRE-MIF/caniuse/master/testcases/{}".format(infile)
        outtest.update({'dataUsed': usedfile})
        if outrun[0]:
            outtest.update({'result': 'Supported'})
        output['results'][formatt][key] = deepcopy(outtest)
    return output

tests_gml = OrderedDict([['gml_file_load', {'data': '../testcases/EMF.BRGM.data.gml',
                                           'check': 'import'}],
                         ['gml_file_display', {'data': '../testcases/EMF.BRGM.data.gml',
                                  'check': 'display'}],
                         ['gml_WFS2_load', {'data': 'https://wfspoc.brgm-rec.fr:443/geoserver/wfs?service=WFS&version=2.0.0&request=GetFeature&typenames=ef%3AEnvironmentalMonitoringFacility&count=100',
                                            'check': 'import'}],
                         ['gml_WFS2_display', {'data': 'https://wfspoc.brgm-rec.fr:443/geoserver/wfs?service=WFS&version=2.0.0&request=GetFeature&typenames=ef%3AEnvironmentalMonitoringFacility&count=100',
                                               'check': 'display'}],
                         ['gml_file_edit', {'data': None,
                                            'check': 'edit'}],
                         ['gml_file_create', {'data': None,
                                              'check': 'create'}],
                         ['gml_size_200m_load', {'data': '../testcases/ES.GFA.AD.gml',
                                                 'check': 'import'}],
                         ['gml_fsize_200m_display', {'data': '../testcases/ES.GFA.AD.gml',
                                                     'check': 'display'}],
                         ['gml_geometry_load', {'data': '../testcases/AD.Spain_full.gml',
                                                'check': 'import'}],
                         ['gml_geometry_display', {'data': '../testcases/AD.Spain_full.gml',
                                                   'check': 'display'}],
                         ['gml_mixed_geometry_load', {'data': '../testcases/PS.Finland.mixed.geometry.gml',
                                                      'check': 'import'}],
                         ['gml_mixed_geometry_display', {'data': '../testcases/PS.Finland.mixed.geometry.gml',
                                                         'check': 'display'}],
                         ['gml_multiple_geometry_load', {'data': None,
                                                         'check': 'import'}],
                         ['gml_multiple_geometry_display', {'data': None,
                                                            'check': 'display'}],
                         ['gml_crs_http_encoding', {'data': None,
                                                    'check': 'display'}],
                         ['gml_geometry_3d_load', {'data': '../testcases/AD.Spain_full.3D.srsDimension.gml',
                                                   'check': 'import'}],
                         ['gml_geometry_3d_display', {'data': '../testcases/AD.Spain_full.3D.srsDimension.gml',
                                                      'check': 'display'}]])

tests_geojson = OrderedDict([['geojson_file_load', {'data': '../testcases/efs_example_2.geojson.geojson',
                                                    'check': 'import'}],
                             ['geojson_file_display', {'data': '../testcases/efs_example_2_more.timeseries.results.geojson',
                                                       'check': 'display'}],
                             ['geojson_file_edit', {'data': '../testcases/efs_example_2.geojson.geojson',
                                                    'check': 'edit'}],
                             ['geojson_file_create', {'data': '../testcases/efs_example_2.geojson.geojson',
                                                      'check': 'create'}],
                             ['geojson_geometry_point_load', {'data': '../testcases/efs_example_2.geojson.geojson',
                                                              'check': 'import'}],
                             ['geojson_geometry_point_display', {'data': '../testcases/efs_example_2_more.timeseries.results.geojson',
                                                                 'check': 'display'}],
                             ['geojson_geometry_geometrycollection_load', {'data': '../testcases/ads_example_1.geojson-2geographicPositions.geojson',
                                                                           'check': 'import'}],
                             ['geojson_geometry_geometrycollection_display', {'data': '../testcases/ads_example_1.geojson-2geographicPositions.geojson',
                                                                              'check': 'display'}],
                             ['geojson_geometry_3d_load', {'data': '../testcases/ads_example_1-3D.geojson.geojson',
                                                           'check': 'import'}],
                             ['geojson_geometry_3d_display', {'data': '../testcases/ads_example_1-3D.geojson.geojson',
                                                              'check': 'display'}],])

ver = g.version(flags='g', stdout_=PIPE)
ver_dict = dict(item.split("=") for item in ver.outputs.stdout.splitlines())
today = str(date.today())
# test GML
gml_json = all_tests('gml', tests_gml)
with open('../results/GML.Tests-GRASS-GIS.v{}.json'.format(ver_dict['version']), 'w') as fi:
    fi.write(json.dumps(gml_json, indent=True))

geojson_json = all_tests('geojson', tests_geojson)
with open('../results/GeoJSON.Tests-GRASS-GIS.v{}.json'.format(ver_dict['version']), 'w') as fi:
    fi.write(json.dumps(geojson_json, indent=True))