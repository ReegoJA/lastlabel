"""Dataset loading with separate evaluation splits and unlabeled features."""

import dataclasses
import hashlib
import json

import numpy as np
from sklearn import datasets
from sklearn import model_selection
from sklearn import preprocessing
from sklearn.feature_extraction import text


@dataclasses.dataclass
class Dataset:
    """Features and oracle labels; only the runner can query the latter."""

    pool_x: object
    pool_y: np.ndarray
    test_x: object
    test_y: np.ndarray
    metadata: dict


def load(spec: dict, seed: int, cache: str, download: bool = False) -> Dataset:
    """Load a binary dataset without fitting transforms on the test split."""
    name = spec["name"]
    if spec["kind"] == "synthetic":
        x, y = datasets.make_classification(
            n_samples=spec.get("samples", 2400),
            n_features=30,
            n_informative=15,
            n_redundant=5,
            weights=[
                1 - spec.get("positive_fraction", 0.5),
                spec.get("positive_fraction", 0.5)
            ],
            class_sep=spec.get("class_sep", 1.0),
            flip_y=0,
            random_state=seed,
        )
        pool_x, test_x, pool_y, test_y = model_selection.train_test_split(
            x,
            y,
            test_size=0.3,
            stratify=y,
            random_state=seed,
        )
        scaler = preprocessing.StandardScaler().fit(pool_x)
        pool_x, test_x = scaler.transform(pool_x), scaler.transform(test_x)
        fingerprint = hashlib.sha256(x.tobytes() + y.tobytes()).hexdigest()
        source = "sklearn.make_classification; 70/30 stratified split"
        classes = ["class 0", "class 1"]
    elif spec["kind"] == "20newsgroups":
        options = dict(
            categories=spec["categories"],
            data_home=cache,
            remove=("headers", "footers", "quotes"),
            shuffle=False,
            download_if_missing=download,
        )
        train = datasets.fetch_20newsgroups(subset="train", **options)
        test = datasets.fetch_20newsgroups(subset="test", **options)
        if len(train.target_names) != 2:
            raise ValueError("Choose exactly two 20 Newsgroups categories.")
        vectorizer = text.TfidfVectorizer(
            min_df=2,
            max_df=0.95,
            max_features=20000,
            sublinear_tf=True,
            ngram_range=(1, 2),
        )
        pool_x = vectorizer.fit_transform(train.data)
        test_x = vectorizer.transform(test.data)
        pool_y, test_y = train.target, test.target
        fingerprint = hashlib.sha256(
            json.dumps(
                [train.data, test.data,
                 pool_y.tolist(),
                 test_y.tolist()],
                ensure_ascii=True,
            ).encode()).hexdigest()
        source = "20 Newsgroups official train/test; headers/footers/quotes removed"
        classes = train.target_names
    else:
        raise ValueError(f"Unknown dataset kind: {spec['kind']}")
    return Dataset(
        pool_x, pool_y, test_x, test_y, {
            "name":
                name,
            "source":
                source,
            "fingerprint":
                fingerprint,
            "pool_size":
                len(pool_y),
            "test_size":
                len(test_y),
            "features":
                pool_x.shape[1],
            "class_names":
                classes,
            "pool_positive_fraction":
                float(pool_y.mean()),
            "test_positive_fraction":
                float(test_y.mean()),
            "preprocessing":
                "Fit on unlabeled pool only (transductive); never on test.",
        })
