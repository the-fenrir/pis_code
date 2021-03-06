# -*- coding: utf-8 -*-
"""Training a Classifier on Extracted Features.

Learn how well extracted features from a pre-trained CNN on ImageNet perform on standaritized
dataset, which have nothing in common with ImageNet.

Examples:
    $ python train_model.py --db ../datasets/animals/hdf5/features.hdf5 --model animals.cpickle

    $ python train_model.py --db ../datasets/caltech-101/hdf5/features.hdf5
                            --model caltech101.cpickle

    $ python train_model.py --db ../datasets/flowers17/hdf5/features.hdf5
                            --model flowers17.cpickle

Attributes:
    db (str):
        Path HDF5 database
    model (path)
        Path to the pre-trained scikit-learn classifier residing on disk
    jobs (int, optional)
        Specify the number of concurrent jobs when running a grid search to tune our
        hyperparameters (default = -1)
"""
import argparse
import pickle
import h5py
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import classification_report


def main():
    """Train a classifier on extracted features.
    """
    # construct the argument parse and parse the arguments
    args = argparse.ArgumentParser()
    args.add_argument("-d", "--db", required=True,
                      help="path HDF5 database")
    args.add_argument("-m", "--model", required=True,
                      help="path to output model")
    args.add_argument("-j", "--jobs", type=int, default=-1,
                      help="# of jobs to run when tuning hyperparameters")
    args = vars(args.parse_args())

    # open the HDF5 database for reading then determine the index of
    # the training and testing split, provided that this data was
    # already shuffled *prior* to writing it to disk
    db = h5py.File(args["db"], "r")
    i = int(db["labels"].shape[0] * 0.75)
    # define the set of parameters that we want to tune then start a
    # grid search where we evaluate our model for each value of C
    print("[INFO] tuning hyperparameters...")
    params = {"C": [0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0]}
    model = GridSearchCV(LogisticRegression(solver="lbfgs", multi_class="auto"),
                         params, cv=3, n_jobs=args["jobs"])
    model.fit(db["features"][:i], db["labels"][:i])
    print("[INFO] best hyperparameters: {}".format(model.best_params_))
    # evaluate the model
    print("[INFO] evaluating...")
    preds = model.predict(db["features"][i:])
    print(classification_report(db["labels"][i:], preds, target_names=db["label_names"]))
    # serialize the model to disk
    print("[INFO] saving model...")
    f = open(args["model"], "wb")
    f.write(pickle.dumps(model.best_estimator_))
    f.close()
    # close the database
    db.close()


if __name__ == "__main__":
    main()
