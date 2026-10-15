# Sources and attribution

LastLabel grows directly from Reego John-Annaselvan's undergraduate research with Dr. Michael Bloodgood at The College of New Jersey. Bloodgood and the coauthors below developed the research foundation. LastLabel implements and extends their ideas to test annotation-cost and predictive-performance trade-offs.

## Research foundations

1. Michael Bloodgood and K. Vijay-Shanker (2009). *A Method for Stopping Active Learning Based on Stabilizing Predictions and the Need for User-Adjustable Stopping.* CoNLL 2009, pages 39-47.
   [ACL Anthology](https://aclanthology.org/W09-1107/).
   Source for SP, fixed random unlabeled stop sets, and agreement windows.
2. Michael Bloodgood and John Grothendieck. *Analysis of Stopping Active Learning
   Based on Stabilizing Predictions.*
   [arXiv:1504.06329](https://arxiv.org/abs/1504.06329).
   Theoretical motivation for connecting agreement to changes in F-measure,
   no unconditional noisy-label guarantee is asserted here.
3. Michael Altschuler and Michael Bloodgood (2019). *Stopping Active Learning
   Based on Predicted Change of F Measure for Text Classification.*
   [arXiv:1901.09118](https://arxiv.org/abs/1901.09118).
   Source for the binary PCF estimate and consecutive-threshold criterion.
4. Kurlandski and Bloodgood (2022). *Impact of Stop Sets on Stopping Active
   Learning for Text Classification.* [arXiv:2201.05460](https://arxiv.org/abs/2201.05460).
   Motivation for comparing fixed stop sets with the remaining unlabeled pool.

The implementation independently follows these definitions. Its logistic
learner, synthetic noise, easy-set stress test, study matrix, and software
architecture are extensions, not claimed as the authors' experimental setup.
The paper authors are credited for research, not listed as software contributors.

## Data and software

- [small-text](https://github.com/webis-de/small-text), Christopher Schröder and contributors, MIT: the required active-learning engine. Cite Christopher Schröder, Lydia Müller, Andreas Niekler, and Martin Potthast (2023), [Small-Text: Active Learning for Text Classification in Python](https://aclanthology.org/2023.eacl-demo.11/), EACL System Demonstrations, pages 84-95. This is the library used during Reego's earlier work with Dr. Bloodgood. The new implementation pins version 1.4.1.
- [dill](https://github.com/uqfoundation/dill), Mike McKerns and contributors, BSD-3-Clause: small-text serialization dependency.
- [tqdm](https://github.com/tqdm/tqdm), tqdm developers, MPL-2.0 and MIT: small-text progress dependency.
- [packaging](https://github.com/pypa/packaging), Python Packaging Authority, BSD-2-Clause or Apache-2.0: version handling.


- [20 Newsgroups](https://scikit-learn.org/stable/datasets/real_world.html#the-20-newsgroups-text-dataset):
  historical newsgroup corpus distributed through scikit-learn's documented
  fetcher, original text is not redistributed in this archive. Follow the
  upstream dataset terms and avoid treating historical posts as current facts.
- [scikit-learn](https://scikit-learn.org/stable/), scikit-learn developers,
  BSD-3-Clause: learners, metrics, synthetic data, preprocessing, corpus loader.
- [NumPy](https://numpy.org/), NumPy developers, BSD-3-Clause: numerical arrays,
  random streams, bootstrap resampling.
- [SciPy](https://scipy.org/), SciPy developers, BSD-3-Clause: numerical/sparse
  infrastructure used by scikit-learn.
- [Matplotlib](https://matplotlib.org/), Matplotlib developers, Matplotlib
  license: scientific figures.
- [threadpoolctl](https://github.com/joblib/threadpoolctl), threadpoolctl
  developers, BSD-3-Clause: bounded native thread pools.
- [pytest](https://docs.pytest.org/), pytest developers, MIT: automated tests.
- [YAPF](https://github.com/google/yapf), Google and contributors, Apache-2.0:
  Python formatting with the Google preset.

- [setuptools](https://setuptools.pypa.io/), Python Packaging Authority and contributors, MIT: package builds.

No library source is vendored. Dependencies retain their own licenses and
notices. The exact installed pilot versions are in `requirements-pilot.txt`
and each result manifest. Project code is MIT-licensed.

Coding-style references:
[awesome-guidelines](https://github.com/Kristories/awesome-guidelines) and its
linked [Google Python guide](https://google.github.io/styleguide/pyguide.html).
