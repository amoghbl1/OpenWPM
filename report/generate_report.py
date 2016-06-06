#!/usr/bin/env python
import os
import jinja2
import sqlite3
from time import time
SQLITE_FILE = os.path.expanduser("~/openwpm/crawl-data.sqlite")
TEMPLATE_FILE = "./template.jinja"
OUTPUT_FILE = "./output.html"

def make_output(headings, rows):
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template(TEMPLATE_FILE)
    rows = list(rows)
    templateVars = { "title" : "Mobile JS scripts",
            "headings" : headings,
            "rows" : rows,
            "len_rows" : len(rows)}
    outputText = template.render( templateVars )
    with open(OUTPUT_FILE, 'w') as f:
        f.write(outputText)
 
def generate_report():
    connection = sqlite3.connect(SQLITE_FILE)
    QUERY="""SELECT site_visits.visit_id, site_visits.site_url, javascript.script_url,
             javascript.parameter_value, javascript.symbol, script_line, script_col
             FROM site_visits, javascript
             WHERE parameter_index = 0 AND javascript.visit_id==site_visits.visit_id
             AND symbol
             LIKE 'window.addEventListener' AND
             parameter_value IN ('deviceorientation', 'devicelight', 'deviceproximity', 'devicemotion')
             ORDER BY javascript.script_url"""
    print QUERY
    t0 = time()
    rows = connection.execute(QUERY)
    print "Query took", (time() - t0), "sec"
    
    headings = list(map(lambda x: x[0], rows.description))
    make_output(headings, rows)

def main():
    generate_report()

if __name__ == '__main__':
      main()
