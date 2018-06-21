import glob
import json
import os
import sys
from os import walk
import imghdr
import csv
import argparse
from os.path import join

from flask import Flask, redirect, url_for, request
from flask import render_template
from flask import send_file

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


@app.route('/tagger')
def tagger():
    if (app.config["HEAD"] == len(app.config["FILES"])):
        return redirect(url_for('bye'))
    directory = app.config['IMAGES']
    image = app.config["FILES"][app.config["HEAD"]]
    labels = app.config["LABELS"]
    not_end = not (app.config["HEAD"] == len(app.config["FILES"]) - 1)
    print(not_end)
    return render_template('tagger.html', not_end=not_end, directory=directory, image=image, labels=labels,
                           label_names=app.config['LABEL_NAMES'],
                           head=app.config["HEAD"] + 1, len=len(app.config["FILES"]))


@app.route('/next')
def next_image():
    image = app.config["FILES"][app.config["HEAD"]]
    app.config["HEAD"] = app.config["HEAD"] + 1
    with open(app.config["OUT"], 'a') as f:
        for label in app.config["LABELS"]:
            f.write(image + "," +
                    label["id"] + "," +
                    label["name"] + "," +
                    str(round(float(label["xMin"]))) + "," +
                    str(round(float(label["xMax"]))) + "," +
                    str(round(float(label["yMin"]))) + "," +
                    str(round(float(label["yMax"]))) + "\n")
    app.config["LABELS"] = []
    return redirect(url_for('tagger'))


@app.route('/')
def main():
    return redirect(url_for('tagger'))


@app.route("/bye")
def bye():
    return send_file("taf.gif", mimetype='image/gif')


@app.route('/add/<id>')
def add(id):
    xMin = request.args.get("xMin")
    xMax = request.args.get("xMax")
    yMin = request.args.get("yMin")
    yMax = request.args.get("yMax")
    label = request.args.get('label')

    app.config["LABELS"].append({"id": id,
                                 "xMin": xMin,
                                 "xMax": xMax,
                                 "yMin": yMin,
                                 "yMax": yMax,
                                 'name': label
                                 })

    return redirect(url_for('tagger'))


@app.route('/remove/<id>')
def remove(id):
    index = int(id) - 1
    del app.config["LABELS"][index]
    for label in app.config["LABELS"][index:]:
        label["id"] = str(int(label["id"]) - 1)
    return redirect(url_for('tagger'))


@app.route('/image/<f>')
def images(f):
    images = app.config['IMAGES']
    return send_file(images + f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type=str, help='specify the config file', required=True)
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    source_dir = config['source_dir']
    if source_dir[-1] != "/":
        source_dir += "/"
    app.config["IMAGES"] = source_dir
    app.config["LABELS"] = []

    image_exts = ['.jpg', '.jpeg', '.png']
    try:
        _, _, files = next(walk(app.config["IMAGES"]))
        files = list(filter(lambda f: os.path.splitext(f)[1] in image_exts, files))
    except StopIteration:
        files = []

    if len(files) == 0:
        print("No files")
        exit()

    app.config["FILES"] = files
    app.config["HEAD"] = 0
    app.config['OUT'] = join(source_dir, 'annotations.csv')

    if len(config.get('label_names', [])) == 0:
        print('No labels')
        exit()

    app.config['LABEL_NAMES'] = config['label_names']

    with open("out.csv", 'w') as f:
        f.write("image,id,name,xMin,xMax,yMin,yMax\n")
    app.run(debug="True")
