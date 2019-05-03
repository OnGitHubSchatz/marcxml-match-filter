# MARCXML Record Filter

## Requirements
Python 3.4+

## Install match_filter
```bash
git clone git@github.com:gitschatz/marcxml-match-filter.git match-filter && cd match-filter
```
### Having just installed Python3 on a Python2.x system
```bash
pip3 install -r requirements.txt
sudo cp match_filter.py /usr/local/bin/match_filter && sudo chmod +x /usr/local/bin/match_filter
```

## Usage
Requires a directory of EPUB files and a MARCXML record collection in valid XML.
```bash
python3 match_filter.py PATH/ MARCXML
```
