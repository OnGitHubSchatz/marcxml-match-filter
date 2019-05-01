#!/usr/bin/env python
from typing import List

import click
import glob
import re
import os
from bs4 import BeautifulSoup


@click.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False))
@click.argument('marcxml', type=click.File(mode='r+'))
def process(path, marcxml):
	index = filenames_to_index(path)

	# Dict with length, collection, soup keys
	parsed = parse_marcxml(marcxml)

	unmatched_ids = diff_index_records(index, parsed['collection'])

	click.echo("Found {} unmatched items to remove".format(len(unmatched_ids)))

	# @todo move to own function
	# snip ----

	unmatched_records = []
	for u in unmatched_ids:
		unmatched_records.append(parsed['soup'].find('marc:datafield', string=u).parent)

	writeable_unmatched_records = list(map(lambda r: str(r), unmatched_records))
	unmatched_records_file = "unmatched_{}_{}".format(len(unmatched_ids), marcxml.name)

	with open(unmatched_records_file, 'w') as urf:
		urf.write(
			'<?xml version="1.0" encoding="UTF-8" ?><marc:collection xmlns:marc="http://www.loc.gov/MARC21/slim" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd">')
		for item in writeable_unmatched_records:
			urf.write("{}".format(item))
		urf.write("</marc:collection>")

	if os.path.realpath(unmatched_records_file):
		click.echo("Created {} in current directory".format(unmatched_records_file))

	# ----snip

	click.echo("Ready to filter file at: {}".format(os.path.realpath(marcxml.name)))

	if click.confirm('Do you want to continue?', abort=True):
		if create_backup(parsed['len'], marcxml):
			if remove_unmatched(unmatched_ids, parsed['soup'], marcxml):
				click.echo("Filtered out unmatched records from {}".format(marcxml.name))


def filenames_to_index(directory):
	# Assuming EPUBs
	epubs = [f for f in glob.glob(directory + "/*.epub")]
	# Assuming a numerical 8-16 char identifier
	scns = [m.group(1) for fname in epubs for m in [re.search("[\s_]?(\d{8,16})\.epub", fname)] if m]
	return scns


def parse_marcxml(marcxml_file):
	marcxml_soup = BeautifulSoup(marcxml_file, features="xml")

	scn_collection = []
	tag_collection = marcxml_soup.find_all('marc:datafield')
	record_length = len(marcxml_soup.find_all('marc:record'))

	for tag in tag_collection:
		if tag.attrs['tag'] == '028' and tag.find('marc:subfield').attrs['code'] == 'a':
			record = tag.parent.find('marc:controlfield', {"tag": "001"}).string
			# list of dicts to allow for duplicates 001's:028's
			scn_collection.append({record: tag.text})

	return {'len': record_length, 'collection': scn_collection, 'soup': marcxml_soup}


def diff_index_records(index, scn_collection):
	# records with a 028 that match entry in index list
	matching_record_ids = []  # type: List[str]

	# @todo list of dict comprehension
	for dic in scn_collection:
		for key, val in dic.items():
			if val in index:
				matching_record_ids.append(str(key.strip()))

	matching_whitelist_uniq = list(dict.fromkeys(matching_record_ids))
	# Subtract the whitelisted matching records from the record ids in collection, left with unmatched record ids
	return list(set([str(*d.keys()).strip() for d in scn_collection]) - set(matching_whitelist_uniq))


def create_backup(length, marcxml):
	command = "cp {} {}_backup.{}".format(marcxml.name, length, marcxml.name)
	if os.system(command) == 0:
		return True


def remove_unmatched(unmatched_ids, soup, marcxml):
	# Decompose the parents (records) of unmatched 001 tags
	for unmatch in unmatched_ids:
		soup.find('marc:controlfield', {"tag": "001"}, string=unmatch).parent.decompose()

	# Replace the file passed in as argument initially.
	marcxml.seek(0)
	marcxml.truncate()
	marcxml.write(str(soup))
	return True


if __name__ == '__main__':
	process()
