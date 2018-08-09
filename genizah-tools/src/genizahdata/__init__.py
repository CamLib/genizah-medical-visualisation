import re
import warnings

from lxml import etree

namespaces = {'tei': 'http://www.tei-c.org/ns/1.0'}
genizah_subject = 'http://id.loc.gov/authorities/subjects/sh85018717.html'

filedesc = '/tei:TEI/tei:teiHeader/tei:fileDesc'
ms_desc = f'{filedesc}/tei:sourceDesc/tei:msDesc'


class GenizahDataWarning(UserWarning):
    pass


# Unfortunatley the metadata uses namespaces in some files and not in others, so we need to match TEI elements with no
# namespace in addition to the TEI namespace.
def _strip_tei_ns(expr):
    return re.sub(r'\btei:', '', expr)


def _xpath_optional_ns(el, expr):
    """Evaluate an xpath expression with and without the tei namespace."""
    return (el.xpath(expr, namespaces=namespaces) or
            el.xpath(_strip_tei_ns(expr)))


def is_genizah_item(root_el):
    return _xpath_optional_ns(root_el, (
        f'boolean(/tei:TEI/tei:teiHeader/tei:profileDesc/'
        f'tei:textClass/tei:keywords//tei:ref[@target="{genizah_subject}"])'))


def is_medical_item(root_el):
    return 'medical' in get_title(root_el).lower()


def get_title(root_el):
    return _xpath_optional_ns(root_el,
                              f'normalize-space({ms_desc}/'
                              f'tei:msContents/tei:msItem[1]/tei:title)')


def get_summary(root_el):
    return _xpath_optional_ns(root_el, f'normalize-space({ms_desc}/'
                                       f'tei:msContents/tei:summary)')


def get_date_range(root_el):
    dates = _xpath_optional_ns(
        root_el, f'{ms_desc}/tei:history/tei:origin/tei:date[1]')

    if dates:
        date = dates[0]
        start = date.attrib['notBefore']
        end = date.attrib['notAfter']
        return (start, end)


def get_material_type(root_el):
    return _xpath_optional_ns(
        root_el, f'normalize-space({ms_desc}'
                 '/tei:physDesc/tei:objectDesc/tei:supportDesc/@material)') or None


def get_fragment_size(root_el):
    dimensions = _xpath_optional_ns(
        root_el, f'{ms_desc}/tei:physDesc/tei:objectDesc/'
                 'tei:supportDesc/tei:extent/tei:dimensions[@unit="cm"][count(*) = 2][tei:height][tei:width]/*/child::text()')

    if dimensions:
        try:
            width, height = (float(x) for x in dimensions)
            return (width, height)
        except ValueError as e:
            warnings.warn(f'non-numeric value for tei:width or tei:height column: {dimensions}',
                          GenizahDataWarning)


def get_layout(root_el):
    layouts = _xpath_optional_ns(
        root_el, f'{ms_desc}/tei:physDesc/tei:objectDesc/tei:layoutDesc/tei:layout[@columns]')
    if not layouts:
        return

    layout = layouts[0]
    try:
        columns = int(layout.attrib['columns'])
    except ValueError as e:
        warnings.warn(f'non-integer value for tei:layout columns attribute: {layout.attrib["columns"]}',
                      GenizahDataWarning)
        return

    lines_expr = re.search(r'\b(\d+) lines\b', layout.text or '')
    if lines_expr:
        return (columns, int(lines_expr.group(1)))


def filename(path):
    return re.sub('^(?:.*/)?([^/]+)\.[a-z]+$', r'\1', path)


def parse_xml(name, file):
    try:
        return etree.parse(file)
    # Some of the TEI files have invalid id attribute values, ignore those
    except etree.XMLSyntaxError as e:
        msg = str(e)
        if 'xml:id' in msg and 'is not an NCName' in msg:
            warnings.warn(f"Ignoring XML file with invalid id attribute: {name}",
                          GenizahDataWarning)
            return None
        raise


def get_data(path, root_el):
    date_range = get_date_range(root_el)
    size = get_fragment_size(root_el)
    layout = get_layout(root_el)
    return {
        'classmark': filename(path),
        'title': get_title(root_el),
        'summary': get_summary(root_el),
        'material': get_material_type(root_el),
        'date_start': date_range[0] if date_range else None,
        'date_end': date_range[1] if date_range else None,
        'width': size[0] if size else None,
        'height': size[1] if size else None,
        'columns': layout[0] if layout else None,
        'lines': layout[1] if layout else None
    }


def extract_tar_xml(tar_archive):
    for entry in tar_archive:
        xml = parse_xml(entry.name, tar_archive.extractfile(entry))

        if xml:
            yield entry.name, xml


def medical_elements(all_els):
    """
    Filter an iterable of (name, element) tuples to include only Genizah medical
    items.

    :param content: An iterable of (name, element) tuples
    :return: The filtered iterable.
    """
    return ((name, el) for name, el in all_els
            if is_genizah_item(el) and is_medical_item(el))
