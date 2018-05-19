# -*- coding: utf-8 -*-
import sys
import argparse
import xlrd
import csv
import re
import datetime
import unicodedata
from rdflib import Graph
from rdflib import URIRef, Literal
from rdflib.namespace import RDFS, RDF

def parse_args(args=sys.argv[1:]):
    """ Get the parsed arguments specified on this script.
    """
    parser = argparse.ArgumentParser(description="")

    parser.add_argument(
        'path_to_properties',
        action='store',
        type=str,
        help='Ful path to the manifest file.')

    return parser.parse_args(args)

#日本語か否かを判定するプログラム
def is_japanese(string):
    for ch in string:
        name = unicodedata.name(ch)
        if "CJK UNIFIED" in name \
        or "HIRAGANA" in name \
        or "KATAKANA" in name:
            return True
    return False

def arrange_str(text):
    #全角半角を正規化
    text = unicodedata.normalize('NFKC', text)
    #改行コード
    text = text.replace("\r\n", "\\r\\n")
    #トリム
    text = text.strip()

    #文字化け対策
    if is_japanese(text):
        text = text + "_nakamura196maeda"

    return text

"""日付のシリアル値をdatetime型に変換するメソッド"""
def get_dt_from_serial(serial):
    base_date = datetime.datetime(1899, 12, 30)
    d, t = re.search(r'(\d+)(\.\d+)', str(serial)).groups()
    return base_date + datetime.timedelta(days=int(d)) \
        + datetime.timedelta(seconds=float(t) * 86400)

"""文字コードがsjisのcsvファイルを作成する（Excelでの確認用）"""
def createFieldSet(schemaPath, fieldSet):

    # imagesの読み込み
    f = open(schemaPath, 'r')

    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if len(row) == 4:
            qname = row[0]
            fieldSet.append(qname)
    f.close()

def createVocabulary(schemaPath, rdfPath):

    g = Graph()

    # imagesの読み込み
    f = open(schemaPath, 'r')

    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if len(row) == 4:
            qname = row[0]
            if(row[3] != ""):
                NS = row[3]
                localName = qname.split(":")[1]
                uri = NS + localName
                g.add((URIRef(uri), RDFS.label, Literal(row[1])))
                g.add((URIRef(uri), RDFS.comment, Literal(row[2])))
                g.add((URIRef(uri), RDF.type, RDF.Property))

    f.close()



    f2 = open(rdfPath, "wb")

    f2.write(g.serialize(format='xml'))
    f2.close()


def main(path_to_properties):

    # 設定ファイルの読み込み
    properties = dict()

    f = open(path_to_properties)
    line = f.readline() # 1行を文字列として読み込む(改行文字も含まれる)

    while line:
        e = line.strip().split("=")
        if len(e) == 2:
            properties[e[0]] = e[1]
        line = f.readline()
    f.close

    collection = properties["COLLECTION_NAME"]

    outputPath = properties["OUTPUT_FILE_PATH"]

    rdfPath = outputPath + "/" + collection + ".rdf";
    csvPath = outputPath + "/" + collection + ".csv";

    fieldSet = []

    schemaPath = properties["SCHEMA_FILE_PATH"]
    if schemaPath != "":
        createFieldSet(schemaPath, fieldSet)
        createVocabulary(schemaPath, rdfPath)

    '''
    omeka_field_set = properties["OMEKA_FIELD_SET"]
    for ofield in omeka_field_set.split(","):
        fieldSet.append(ofield)
    '''

    RECORD_ID_FIELD = properties["RECORD_ID_FIELD"];

    book = xlrd.open_workbook(properties["METADATA_FILE_PATH"])
    sheet = book.sheet_by_index(0)

    labelMap = dict()

    RECORD_ID_INDEX = -1

    for col_index in range(0, sheet.ncols):
        val = sheet.cell_value(rowx=0, colx=col_index)
        labelMap[col_index] = val

        if val == RECORD_ID_FIELD:
            RECORD_ID_INDEX = col_index

    map = dict()

    for row_index in range(1, sheet.nrows):

        record_id = str(sheet.cell_value(rowx=row_index, colx=RECORD_ID_INDEX)).strip()

        if len(record_id) == 0:
            continue

        tmpMap = dict()
        map[record_id] = tmpMap

        for col_index in labelMap:
            cell = sheet.cell(rowx=row_index, colx=col_index)

            # val = ""

            if cell.ctype == xlrd.XL_CELL_NUMBER:  # 数値
                val = cell.value

                if val.is_integer():
                    # 整数に'.0'が付与されていたのでintにcast
                    val = int(val)

            elif cell.ctype == xlrd.XL_CELL_DATE:  # 日付
                dt = get_dt_from_serial(cell.value)
                val = dt.strftime('%Y-%m-%d')

            else:  # その他
                val = cell.value

            if len(str(val)) > 0:
                tmpMap[labelMap[col_index]] = val

    f = open(csvPath, 'w')

    writer = csv.writer(f, lineterminator='\n')

    '''ヘッダー行の作成'''
    list0 = []
    list0.append("Identifier")
    list0.append("Title");
    list0.append("Resource Type");
    list0.append("Collection Identifier");

    list0.append("Resource Class");

    list0.append("resource template");

    list0.append("dcterms:publisher");
    list0.append("dcterms:rights");
    list0.append("dcterms:date");
    list0.append("dcterms:description");

    list0.append("rdfs:seeAlso");
    list0.append("dcterms:isPartOf");
    list0.append("dcterms:relation");
    list0.append("foaf:thumbnail");

    list0.append("dcterms:references"); #Manifest
    list0.append("sc:attributionLabel");
    list0.append("sc:viewingDirection");
    list0.append("sc:viewingHint");



    for field in fieldSet:
        list0.append(field);

    writer.writerow(list0)

    '''Item Set行の作成'''
    list1 = []
    list1.append(collection);
    list1.append(collection);
    list1.append("Item Set");

    for col_index in range(0, len(list0)-3):
        list1.append("")

    writer.writerow(list1)

    index = 0

    props = ["YEAR_FIELD", "DESC_FIELD", "SEEALSO_FIELD", "WITHIN_FIELD", "URL_FIELD", "THUMBNAIL_FIELD", "MANIFEST_FIELD", "ATTRIBUTION_FIELD", "VIEWINGDIRECTION_FIELD", "VIEWINGHINT_FIELD"]

    for record_id in map:
        list = []
        list.append(record_id)

        if index % 100 == 0:
            print(str(index)+"/"+str(len(map))+"="+record_id)

        index = index + 1

        metaMap = map[record_id]

        list.append(arrange_str(metaMap[properties["TITLE_FIELD"]]))

        list.append("Item")
        list.append(collection)

        list.append("dctype:Image")

        list.append(collection)

        list.append(arrange_str(metaMap[properties["COLLECTION_FIELD"]]))
        list.append(metaMap[properties["RIGHT_FIELD"]])

        for prop in props:
            value = ""

            if prop in properties and properties[prop] in metaMap:
                value = metaMap[properties[prop]]


            if prop == "DESC_FIELD":
                tmp2 = "tmp2"
            list.append(arrange_str(value))

        for field in fieldSet:
            value = ""
            if field in metaMap:
                value = metaMap[field]
            list.append(arrange_str(str(value)))

        writer.writerow(list)

    f.close()

if __name__ == "__main__":
    args = parse_args()

    main(
        args.path_to_properties)
