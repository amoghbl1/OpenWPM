#!/usr/bin/env python
import os
import jinja2
import sqlite3
from time import time
from _collections import defaultdict
SQLITE_FILE = os.path.expanduser("~/openwpm/100k_16browsers/crawl-data.sqlite")
SQLITE_FILE = os.path.expanduser("~/openwpm/100k_32browsers/crawl-data.sqlite")
# SQLITE_FILE = os.path.expanduser("~/openwpm/13k_8browsers/crawl-data.sqlite")

TEMPLATE_FILE = "./template.jinja"
OUTPUT_FILE = "./output.html"

def make_output(headings, rows):
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template(TEMPLATE_FILE)
    templateVars = { "title" : "Mobile JS scripts",
            "headings" : headings,
            "rows" : rows,
            "len_rows" : len(rows)}
    outputText = template.render( templateVars )
    with open(OUTPUT_FILE, 'w') as f:
        f.write(outputText)

def db_query(qry_str):
    connection = sqlite3.connect(SQLITE_FILE)
    print qry_str
    t0 = time()
    rows = connection.execute(qry_str)
    headings = list(map(lambda x: x[0], rows.description))
    rows = rows.fetchall()
    print "Query took", (time() - t0), "sec"
    return rows, headings

def print_script_freq_dist(script_freqs):
    for script_url, url_set in script_freqs.iteritems():
        if len(url_set) > 10:
            print script_url, len(url_set)

def get_stats(rows):
    all_sites = set()
    all_scripts = set()
    deviceorientation_scripts = set()
    devicelight_scripts = set()
    deviceproximity_scripts = set()
    devicemotion_scripts = set()

    deviceorientation_sites = set()
    devicelight_sites = set()
    deviceproximity_sites = set()
    devicemotion_sites = set()

    script_freq = defaultdict(set)
    script_freq_deviceorientation = defaultdict(set)
    script_freq_devicelight = defaultdict(set)
    script_freq_deviceproximity = defaultdict(set)
    script_freq_devicemotion = defaultdict(set)
    for row in rows:
        # print row
        site_url, script_url, api_type = row[1:4]
        all_sites.add(site_url)
        all_scripts.add(script_url)
        script_freq[script_url].add(site_url)
        if api_type == "deviceorientation":
            deviceorientation_scripts.add(script_url)
            deviceorientation_sites.add(site_url)
            script_freq_deviceorientation[script_url].add(site_url)
        elif api_type == "devicelight":
            devicelight_scripts.add(script_url)
            devicelight_sites.add(site_url)
            script_freq_devicelight[script_url].add(site_url)
        elif api_type == "deviceproximity":
            deviceproximity_scripts.add(script_url)
            deviceproximity_sites.add(site_url)
        elif api_type == "devicemotion":
            script_freq_deviceproximity[script_url].add(site_url)
            devicemotion_scripts.add(script_url)
            devicemotion_sites.add(site_url)
            script_freq_devicemotion[script_url].add(site_url)

    print "Total sites", len(all_sites)
    print "Total scripts", len(all_scripts)
    print "deviceorientation scripts", len(deviceorientation_scripts)
    print "deviceorientation sites", len(deviceorientation_sites)
    print "devicelight scripts", len(devicelight_scripts)
    print "devicelight sites", len(devicelight_sites)
    print "deviceproximity scripts", len(deviceproximity_scripts)
    print "deviceproximity sites", len(deviceproximity_sites)
    print "devicemotion scripts", len(devicemotion_scripts)
    print "devicemotion sites", len(devicemotion_sites)
    for freq_set in [script_freq,
                     script_freq_deviceorientation,
                     script_freq_devicelight,
                     script_freq_deviceproximity,
                     script_freq_devicemotion]:
        print "********"
        print_script_freq_dist(freq_set)

def generate_report():
    qry_all_sensor_access ="""SELECT site_visits.visit_id, site_visits.site_url, javascript.script_url,
             javascript.parameter_value, javascript.symbol, script_line, script_col
             FROM site_visits, javascript
             WHERE parameter_index = 0 AND javascript.visit_id==site_visits.visit_id
             AND symbol
             LIKE 'window.addEventListener' AND
             parameter_value IN ('deviceorientation', 'devicelight', 'deviceproximity', 'devicemotion')
             GROUP BY javascript.script_url, site_visits.site_url, javascript.parameter_value
             ORDER BY javascript.script_url"""
    rows, headings = db_query(qry_all_sensor_access)
    get_stats(rows)
    #headings = list(map(lambda x: x[0], rows.description))
    make_output(headings, rows)

def main():
    generate_report()

if __name__ == '__main__':
      main()
