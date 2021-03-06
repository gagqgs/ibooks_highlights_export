#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jinja2 import Environment, FileSystemLoader
from glob import glob
import os
import sqlite3
import datetime
import argparse


PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    loader=FileSystemLoader(os.path.join(PATH, 'templates')),
    trim_blocks=False)


asset_title_tab = {}
base1 = "~/Library/Containers/com.apple.iBooksX/Data/Documents/AEAnnotation/"
base1 = os.path.expanduser(base1)
sqlite_file = glob(base1 + "*.sqlite")

if not sqlite_file:
    print "Couldn't find the iBooks database. Exiting."
    exit()
else:
    sqlite_file = sqlite_file[0]

base2 = "~/Library/Containers/com.apple.iBooksX/Data/Documents/BKLibrary/"
base2 = os.path.expanduser(base2)
assets_file = glob(base2 + "*.sqlite")

if not assets_file:
    print "Couldn't find the iBooks assets database. Exiting."
    exit()
else:
    assets_file = assets_file[0]

db1 = sqlite3.connect(sqlite_file, check_same_thread=False)
cur1 = db1.cursor()

db2 = sqlite3.connect(assets_file, check_same_thread=False)
cur2 = db2.cursor()

def get_all_titles():
    global cur2
    res = cur2.execute("select ZASSETID, ZTITLE, ZAUTHOR from ZBKLIBRARYASSET;").fetchall()
    m = {}
    for r in res:
        m[r[0]] = {"ZTITLE": r[1], "ZAUTHOR": r[2]}

    return m


def get_all_relevant_assetids_and_counts():
    global cur1
    q = "select count(*), ZANNOTATIONASSETID from ZAEANNOTATION where ZANNOTATIONREPRESENTATIVETEXT IS NOT NULL group by ZANNOTATIONASSETID;"
    res = cur1.execute(q).fetchall()
    return res

def get_all_relevant_titles():
    aids_and_counts = get_all_relevant_assetids_and_counts()
    print aids_and_counts
    all_titles = get_all_titles()

    op = {}

    for cnt, aid in aids_and_counts:
        all_titles[aid]["COUNT"] = cnt
        op[aid] = all_titles[aid]

    return op

def bold_text(selected_text, representative_text):
    left = representative_text.find(selected_text)
    right = left + len(selected_text)

    op = representative_text[:left] + "<b>" +  representative_text[left:right] + "</b>" + representative_text[right:]
    return op

def get_book_details(assetid):
    global cur2
    res2 = cur2.execute("select ZTITLE, ZAUTHOR from ZBKLIBRARYASSET where ZASSETID=?", (assetid,))
    t =  res2.fetchone()
    return t[0] + ", " + t[1]

def get_all_highlights():
    global cur1
    res1 = cur1.execute("select ZANNOTATIONASSETID, ZANNOTATIONREPRESENTATIVETEXT, ZANNOTATIONSELECTEDTEXT, ZANNOTATIONSTYLE from ZAEANNOTATION order by ZANNOTATIONASSETID;")

    return res1


def get_asset_title_tab():
    global cur2

    res2 = cur2.execute("select distinct(ZASSETID), ZTITLE, ZAUTHOR from ZBKLIBRARYASSET")
    for assetid, title, author in res2:
        asset_title_tab[assetid] = [title, author]

    return asset_title_tab


def get_color(num):
    if num == 0:
        return "b_gray"
    elif num == 1:
        return "b_green"
    elif num == 2:
        return "b_blue"
    elif num == 3:
        return "b_yellow"
    elif num == 4:
        return "b_pink"
    elif num == 5:
        return "b_violet"
    else:
        return "b_gray"


template = TEMPLATE_ENVIRONMENT.get_template("simpletemplate.html")
template.globals['bold_text'] = bold_text
template.globals['get_color'] = get_color
template.globals['get_book_details'] = get_book_details

res1 = cur1.execute("select ZANNOTATIONASSETID, ZANNOTATIONREPRESENTATIVETEXT, ZANNOTATIONSELECTEDTEXT, ZANNOTATIONSTYLE from ZAEANNOTATION order by ZANNOTATIONASSETID;")
today = datetime.date.isoformat(datetime.date.today())


# beginning another way of doing the same thing, just more efficient
res2 = cur2.execute("select distinct(ZASSETID), ZTITLE, ZAUTHOR from ZBKLIBRARYASSET")
for assetid, title, author in res2:
    asset_title_tab[assetid] = [title, author]

parser = argparse.ArgumentParser(description='iBooks Highlights Exporter')
parser.add_argument('-o', action="store", default="output.html", dest="fname",
        help="Specify output filename (default: output.html)")
parser.add_argument('--notoc', action="store_true", help="Disable the javascript TOC in the output")
parser.add_argument('--nobootstrap', action="store_true", help="Disable the bootstrap library in the output")
args = parser.parse_args()


with open(args.fname, 'w') as f:
    html = template.render(obj={"last":"###", "date":today, "highlights":res1,
        "assetlist":asset_title_tab, "notoc":args.notoc,
        "nobootstrap":args.nobootstrap})
    f.write(html.encode('utf-8'))
