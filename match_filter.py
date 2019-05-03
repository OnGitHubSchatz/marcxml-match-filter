#!/usr/bin/env python3

from bs4 import BeautifulSoup
from typing import List
import click
import glob
import re
import os
import time

@click.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False))
@click.argument('marcxml', type=click.File(mode='r+'))
def process(path, marcxml):
	process_start = time.time()
	index = filenames_to_index(path)

	# Dict with length, collection, soup keys
	parsed = parse_marcxml(marcxml)

	unmatched_record_ids = diff_index_records(index, parsed['collection'])
	if len(unmatched_record_ids) is not 0:
		click.echo("Found {} unmatched items to remove".format(len(unmatched_record_ids)))
	else:
		click.echo("No unmatched items found. Exiting.")
		exit(0)

	# @todo move to own function
	# snip ----

	unmatched_records = []
	with click.progressbar(unmatched_record_ids, label="Collecting unmatchable records from set...") as bar:
		for u in bar:
			try:
				unmatched_records.append(parsed['soup'].find('marc:controlfield', string=u).parent)
			except AttributeError:
				click.echo("A parent marc:record element was not found for 001: {}. Skipping...".format(u))

	writeable_unmatched_records = list(map(lambda r: str(r), unmatched_records))
	unmatched_records_file = "{}_unmatchable_{}".format(len(unmatched_record_ids), os.path.split(marcxml.name)[1] if os.path.dirname(marcxml.name) is not '' else marcxml.name)

	with open(unmatched_records_file, 'w') as urf:
		urf.write(
			'<?xml version="1.0" encoding="UTF-8" ?><marc:collection xmlns:marc="http://www.loc.gov/MARC21/slim" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd">')
		with click.progressbar(writeable_unmatched_records, label="Exporting unmatchable records...") as bar:
			for item in bar:
				urf.write("{}".format(item))
		urf.write("</marc:collection>")

	if os.path.exists(unmatched_records_file):
		click.echo("Created {} in current directory".format(unmatched_records_file))
		# print('{0:0.1f} second execution'.format(time.time() - process_start))

	# ----snip

	click.echo("Ready to filter file at: {}".format(os.path.realpath(marcxml.name)))

	if click.confirm('Do you want to continue?', abort=True):
		filter_start = time.time()
		if create_backup(parsed['len'], marcxml):
			if remove_unmatched(unmatched_record_ids, parsed['soup'], marcxml):
				click.echo("Filtered out {} unmatched records from {}".format(len(unmatched_record_ids), marcxml.name))
				# print('{0:0.1f} second execution'.format(time.time() - filter_start))


def filenames_to_index(directory):
	# Assuming EPUBs
	epubs = [f for f in glob.glob(directory + "/*.epub")]
	# Assuming a numerical 8-16 char identifier
	scns = [m.group(1) for fname in epubs for m in [re.search("[\s_]?(\d{8,16}X?)\.epub", fname)] if m]
	return scns


def parse_marcxml(marcxml_file):
	marcxml_soup = BeautifulSoup(marcxml_file, features="xml")

	# Bug? Extra XML ProcessingInstruction appears as last element, extract it.
	check_extra = marcxml_soup.contents
	if len(check_extra) > 1:
		check_extra[1].extract()

	scn_collection = []  # type: List[str]
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
	command = "cp {} {}.backup".format(marcxml.name, marcxml.name)
	if os.system(command) == 0:
		return True


def remove_unmatched(unmatched_ids, soup, marcxml):
	# Decompose the parents (records) of unmatched 001 tags
	with click.progressbar(unmatched_ids, label="Removing unmatchable records...") as bar:
		for unmatch in bar:
			soup.find('marc:controlfield', {"tag": "001"}, string=unmatch).parent.decompose()

	# Replace the file passed in as argument initially.
	marcxml.seek(0)
	marcxml.truncate()
	# Scrub double newlines and cast as string
	marcxml.write(re.sub('[\n]{2}', '', str(soup)))
	return True


if __name__ == '__main__':
	process()
