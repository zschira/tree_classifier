import json
import argparse
from src.detector import Detector

parser = argparse.ArgumentParser(description='Manage tree classification/detection')
parser.add_argument('model')
parser.add_argument('-t', '--train', default=False, nargs='?', const=True)
parser.add_argument('-p', '--predict', default=False, nargs='?', const=True)
parser.add_argument('-P', '--preprocess', default=False, nargs='?', const=True)
parser.add_argument('-l', '--load_weights', default=False, nargs='?', const=True)
args = parser.parse_args()

with open('config') as f:
    config = json.load(f)

if args.model == 'detector':
    runner = Detector()

if args.preprocess:
    if type(args.preprocess) is str:
        base_direc = args.preprocess
    else:
        base_direc = config.get('base_direc')

    runner.preprocess(base_direc, config.get('save_direc'))

if args.load_weights:
    if type(args.load_weights) is str:
        weights_path = args.load_weights
    else:
        weights_path = config['load_weights']

if args.train:
    if type(args.train) is str:
        train_direc = args.train
    else:
        train_direc = config.get('train_direc')

    runner.fit_model(train_direc, weights_path)

if args.predict:
    if type(args.predict) is str:
        test_direc = args.predict
    else:
        test_direc = config.get('test_direc')

    runner.create_paths(test_direc, weights_path)