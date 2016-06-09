#!/usr/bin/env python
import os
import jinja2
import sqlite3
from time import time
from _collections import defaultdict
# SQLITE_FILE = os.path.expanduser("~/openwpm/100k_16browsers/crawl-data.sqlite")
# SQLITE_FILE = os.path.expanduser("~/openwpm/100k_32browsers/crawl-data.sqlite")
# SQLITE_FILE = os.path.expanduser("~/openwpm/13k_8browsers/crawl-data.sqlite")
SQLITE_FILE = os.path.expanduser("~/openwpm/crawl-data.sqlite")

TEMPLATE_FILE = "./template.jinja"
OUTPUT_FILE = "./output.html"
SCRIPT_INFO_JINJA = "./script_info.jinja"
SCRIPT_INFO_OUTPUT = "./script_details/"


def write_to_file(path, txt):
    with open(path, 'w') as f:
        f.write(txt)


def make_output(headings, rows):
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template(TEMPLATE_FILE)
    script_info_template = templateEnv.get_template(SCRIPT_INFO_JINJA)
    overview, all_scripts = get_stats(rows)
    # Get script popularity to add to the rows
    counts = defaultdict(int)
    for row in rows:
        counts[row[2]] += 1
    # Information and headings are shown on the first page
    # details are shown on the script specific pages.
    all_scripts_information, all_scripts_headings, all_scripts_details =\
        get_calls_by_scripts(all_scripts, counts)
    template_vars = {"title": "Mobile JS scripts",
                     "general_headings": headings,
                     "general_rows": rows,
                     "scripts_headings": all_scripts_headings,
                     "scripts_rows": all_scripts_information,
                     "overview": overview}
    output_text = template.render(template_vars)
    write_to_file(OUTPUT_FILE, output_text.encode('utf-8').strip())

    script_id = 0

    for script_url, script_details in all_scripts_details.iteritems():
        headings = []
        rows = []
        for i in script_details:
            rows.append(i)
        js_template_vars = {"title": "Information about: " + script_url,
                            "general_headings": headings,
                            "general_rows": rows}
        output_text = script_info_template.render(js_template_vars)
        if not os.path.isdir(SCRIPT_INFO_OUTPUT):
            os.mkdir(SCRIPT_INFO_OUTPUT)
        js_file_name = "%s%s.html" % (SCRIPT_INFO_OUTPUT, str(script_id))
        write_to_file(js_file_name, output_text.encode('utf-8').strip())
        script_id += 1


def db_query(qry_str, fetch_rows=True):
    connection = sqlite3.connect(SQLITE_FILE)
    print qry_str
    t0 = time()
    rows = connection.execute(qry_str)
    headings = list(map(lambda x: x[0], rows.description))
    if fetch_rows:
        rows = rows.fetchall()
    print "Query took", (time() - t0), "sec"
    return rows, headings


def print_script_freq_dist(script_freqs):
    for script_url, url_set in script_freqs.iteritems():
        if len(url_set) > 10:
            print script_url, len(url_set)


# Returns all the information of each script, based on the ids
def get_calls_by_scripts(script_urls, script_popularity_count):
    calls_overview = []
    script_call_count = defaultdict(int)
    script_call_details = defaultdict(set)
    qry = """SELECT * FROM javascript"""
    all_script_calls, _ = db_query(qry, fetch_rows=False)
    script_id = 0
    for script_call in all_script_calls:
        script_url = script_call[3]
        if script_url in script_urls:
            script_call_count[script_url] += 1
            # Assign a uniqe ID for the script
            if script_call_count[script_url] == 1:
                script_id += 1
            # Add myself to the dictionary of this url
            script_call_details[script_url].add(script_call)

    script_id = 0
    headings = ("Script URL", "Popularity (# Sites found on)", "Number of calls")
    for i in script_call_count:
        calls_overview.append((i, script_popularity_count.get(i), script_call_count.get(i), script_id))
        script_id += 1
    return calls_overview, headings, script_call_details


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

    stats = []
    stats.append(("Total sites", len(all_sites)))
    stats.append(("Total scripts", len(all_scripts)))
    stats.append(("deviceorientation scripts", len(deviceorientation_scripts)))
    stats.append(("deviceorientation sites", len(deviceorientation_sites)))
    stats.append(("devicelight scripts", len(devicelight_scripts)))
    stats.append(("devicelight sites", len(devicelight_sites)))
    stats.append(("deviceproximity scripts", len(deviceproximity_scripts)))
    stats.append(("deviceproximity sites", len(deviceproximity_sites)))
    stats.append(("devicemotion scripts", len(devicemotion_scripts)))
    stats.append(("devicemotion sites", len(devicemotion_sites)))

    for freq_set in [script_freq,
                     script_freq_deviceorientation,
                     script_freq_devicelight,
                     script_freq_deviceproximity,
                     script_freq_devicemotion]:
        print "********"
        print_script_freq_dist(freq_set)
    return stats, all_scripts


def generate_report():
    qry_all_sensor_access = """SELECT site_visits.visit_id, site_visits.site_url,
            javascript.script_url, javascript.parameter_value,
            javascript.symbol, script_line, script_col
            FROM site_visits, javascript
            WHERE parameter_index = 0 AND
            javascript.visit_id==site_visits.visit_id
            AND symbol LIKE 'window.addEventListener' AND
            parameter_value IN
            ('deviceorientation', 'devicelight',
            'deviceproximity', 'devicemotion')
            GROUP BY javascript.script_url, site_visits.site_url,
            javascript.parameter_value
            ORDER BY javascript.script_url"""
    rows, headings = db_query(qry_all_sensor_access)
    # get_stats(rows)
    make_output(headings, rows)


def main():
    generate_report()

if __name__ == '__main__':
    main()
