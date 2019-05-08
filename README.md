# MARCXML Record Filter

## Requirements
Python 3.4+

## Grab repo or release
```bash
git clone git@github.com:gitschatz/marcxml-match-filter.git match-filter && cd match-filter
```
or:
[Download latest archive](https://github.com/gitschatz/marcxml-match-filter/releases/latest) and unpack to a staging folder.

### Install requirements and script locally
```bash
pip3 install -r requirements.txt
sudo cp match_filter.py /usr/local/bin/match_filter && sudo chmod +x /usr/local/bin/match_filter
```

## Usage
Requires a directory of EPUB files and a MARCXML record collection in valid XML.
```bash
match_filter SOURCE MARCXML

Options:
-t, --text-file
```
```bash
match_filter --help
```
