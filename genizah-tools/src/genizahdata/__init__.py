import re
import csv
import sys

from lxml import etree
import docopt



_namespaces = {'tei': 'http://www.tei-c.org/ns/1.0'}
_genizah_subject = 'http://id.loc.gov/authorities/subjects/sh85018717.html'

_filedesc = '/tei:TEI/tei:teiHeader/tei:fileDesc'
_ms_desc = f'{_filedesc}/tei:sourceDesc/tei:msDesc'


def _strip_tei_ns(pattern):
    return re.sub(r'\btei:', '', pattern)


def _xpath_optional_ns(el, pattern):
    return (el.xpath(pattern, namespaces=_namespaces) or
            el.xpath(_strip_tei_ns(pattern)))


def is_genizah_item(root_el):
    return _xpath_optional_ns(root_el, (
        f'boolean(/tei:TEI/tei:teiHeader/tei:profileDesc/'
        f'tei:textClass/tei:keywords//tei:ref[@target="{_genizah_subject}"])'))


def is_medical_item(root_el):
    return 'medical' in get_title(root_el).lower()


def get_title(root_el):
    return _xpath_optional_ns(root_el,
                              f'normalize-space({_ms_desc}/'
                              f'tei:msContents/tei:msItem[1]/tei:title)')


def get_summary(root_el):
    return _xpath_optional_ns(root_el, f'normalize-space({_ms_desc}/'
                                       f'tei:msContents/tei:summary)')


def get_date_range(root_el):
    dates = _xpath_optional_ns(
        root_el, f'{_ms_desc}/tei:history/tei:origin/tei:date[1]')

    if dates:
        date = dates[0]
        start = date.attrib['notBefore']
        end = date.attrib['notAfter']
        return [start, end]


_extract_genizah_titles_cmd_usage = '''
usage: genizah-titles [options] <file>...

options:

'''

def parse_all(files):
    for f in files:
        try:
            yield f, etree.parse(f)
        except etree.XMLSyntaxError as e:
            print(f'Error: Invalid XML file: {f}', file=sys.stderr)

def extract_genizah_titles_cmd():
    args = docopt.docopt(_extract_genizah_titles_cmd_usage)

    names = 'path title summary date_start date_end'.split()
    writer = csv.DictWriter(sys.stdout, fieldnames=names)

    xml_content = parse_all(args['<file>'])

    writer.writerows(get_info(f, x) for (f, x) in xml_content if
                  is_genizah_item(x) and is_medical_item(x))


def get_info(file_path, root_el):
    info = dict(path=file_path,
                title=get_title(root_el),
                summary=get_summary(root_el))

    info.update(dict(zip(('date_start', 'date_end'),
                         get_date_range(root_el) or [None] * 2)))

    return info
