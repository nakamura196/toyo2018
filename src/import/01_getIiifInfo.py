# -*- coding: utf-8 -*-
import json
import sys
import csv
import urllib.request, json
import argparse

def parse_args(args=sys.argv[1:]):
    """ Get the parsed arguments specified on this script.
    """
    parser = argparse.ArgumentParser(description="")

    parser.add_argument(
        'inputPath',
        action='store',
        type=str,
        help='Ful path to csv file of ids.')

    parser.add_argument(
        'endpoint',
        action='store',
        type=str,
        help='url to endpoint.')

    return parser.parse_args(args)

def getThumbnail(media_iri):

    response = urllib.request.urlopen(media_iri)
    response_body = response.read().decode("utf-8")
    data = json.loads(response_body.split('\n')[0])

    return data["o:thumbnail_urls"]["square"]

def main(inputPath, endpoint):

    outputPath = inputPath+"_withIiifInfo.csv"

    # endpoint = "https://iiif.dl.itc.u-tokyo.ac.jp/repo"

    ids = []

    with open(inputPath, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)  # ヘッダーを読み飛ばしたい時

        for row in reader:

            id = row[0]
            ids.append(id)

    fo = open(outputPath, 'w')
    writer = csv.writer(fo, lineterminator='\n')
    writer.writerow(["Identifier", "OmekaID", "Thumbnail"])

    for i in range(0, len(ids)):
        id = ids[i]
        if i % 10 == 0:
            print(str(i)+"/"+str(len(ids))+"\t"+id)

        url = endpoint+"/api/items?search="+id

        response = urllib.request.urlopen(url)
        response_body = response.read().decode("utf-8")
        data = json.loads(response_body.split('\n')[0])

        if len(data) == 1:
            data = data[0]
            omeka_id = data["o:id"]
            thumbnail_url = ""
            if len(data["o:media"]) > 0:
                media_iri = data["o:media"][0]["@id"]
                thumbnail_url = getThumbnail(media_iri)
            writer.writerow([id, omeka_id, thumbnail_url])

    f.close()


    print("outputPath:\t"+outputPath)

if __name__ == "__main__":
    args = parse_args()

    main(
        args.inputPath,
        args.endpoint)
