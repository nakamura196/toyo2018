# -*- coding: utf-8 -*-
import json
import sys
import csv
import urllib.request
import requests
import shutil
import base64
import os
import argparse
from xml.dom.minidom import parseString

def parse_args(args=sys.argv[1:]):
    """ Get the parsed arguments specified on this script.
    """
    parser = argparse.ArgumentParser(description="")

    parser.add_argument(
        'csv_path',
        action='store',
        type=str,
        help='path to csv of IIIF manifest List.')

    parser.add_argument(
        'dir_path',
        action='store',
        type=str,
        help='Path to dir.')

    parser.add_argument(
        'api_key',
        action='store',
        type=str,
        help='api key.')

    return parser.parse_args(args)

def download_img(url, file_name):
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(file_name, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
    else:
        print(r.status_code)

def detect_text(path, api_key):

    with open(path, 'rb') as image_file:
        content = base64.b64encode(image_file.read())
        content = content.decode('utf-8')

    url = "https://vision.googleapis.com/v1/images:annotate?key=" + api_key
    headers = { 'Content-Type': 'application/json' }
    request_body = {
        'requests': [{
            'image': {
                'content': content
            },
            'features': [{
                "type": "TEXT_DETECTION"
            }]
        }]
    }
    response = requests.post(
        url,
        json.dumps(request_body),
        headers
    )
    result = response.json()
    # print(result)

    text = ""
    try:
        textAnnotations = result["responses"][0]["textAnnotations"];
        text = textAnnotations[0]["description"]
    except:
        pass

    return text

def createXml(texts, id, outputpath):


    with open('temp.txt', 'r') as myfile:
        xml_template=myfile.read()
        dom = parseString(xml_template)

        # channelノードを取得
        titleStmt = dom.getElementsByTagName("titleStmt")[0]

        # itemノードを生成
        title = dom.createElement('title')
        title.appendChild(dom.createTextNode(id))
        # channelノードに追加
        titleStmt.appendChild(title)

        # channelノードを取得
        body = dom.getElementsByTagName("body")[0]

        for i in range(0, len(texts)):
            page = i + 1

            text = texts[i]["text"]
            url = texts[i]["url"]

            # itemノードを生成
            pb = dom.createElement('pb')
            body.appendChild(pb)

            facs_attr = dom.createAttribute('facs')
            facs_attr.value = url
            pb.setAttributeNode(facs_attr)

            facs_attr = dom.createAttribute('n')
            facs_attr.value = str(page)
            pb.setAttributeNode(facs_attr)

            # itemノードを生成
            p = dom.createElement('p')
            body.appendChild(p)
            p.appendChild(dom.createTextNode(text))

        f = open(outputpath, 'w') # 書き込みモードで開く
        f.write(dom.toprettyxml()) # 引数の文字列をファイルに書き込む
        f.close() # ファイルを閉じる

        # domをxmlに変換して整形
        # print (dom.toprettyxml())


def readManifest(manifest_url, dir_path, api_key):

    id = manifest_url.split("/")[6]

    res = urllib.request.urlopen(manifest_url)
    # json_loads() でPythonオブジェクトに変換
    data = json.loads(res.read().decode('utf-8'))

    canvases = data["sequences"][0]["canvases"]

    oDir = dir_path+"/"+id
    if not os.path.exists(oDir):
        os.makedirs(oDir)
    iDir = oDir+"/images"
    if not os.path.exists(iDir):
        os.makedirs(iDir)

    texts = []

    for i in range(0, len(canvases)):
        print(str(i+1)+"/"+str(len(canvases)))

        canvas = canvases[i]

        if "@id" in canvas["thumbnail"]:
            thumbnail = canvas["thumbnail"]["@id"]
            original = thumbnail.replace("200,200", "full")

            download_img(original, iDir+"/"+ '{0:03d}'.format(i+1)+".jpg")

            text = detect_text(iDir+"/"+ '{0:03d}'.format(i+1)+".jpg", api_key)
            map = dict()
            map["text"] = text
            map["url"] = original
            texts.append(map)

    createXml(texts, id, oDir+"/"+id+".xml")


def main(csv_path, dir_path, api_key):

    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)  # ヘッダーを読み飛ばしたい時

        for row in reader:
            manifest_url = row[0]
            print(manifest_url)
            readManifest(manifest_url, dir_path, api_key)



if __name__ == "__main__":
    args = parse_args()

    main(
        args.csv_path, args.dir_path, args.api_key)
