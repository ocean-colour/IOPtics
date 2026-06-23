============
Installation
============

IOPtics targets **Python ≥ 3.12** and is developed in the ``ocean14`` conda
environment.

From source
-----------

.. code-block:: bash

   git clone https://github.com/ocean-colour/IOPtics.git
   cd IOPtics
   pip install -e .

Sibling packages
----------------------

IOPtics is a thin orchestration layer over two sibling packages it does not
own. They are not on PyPI, so install them from source (the pinned
``requirements.txt`` pulls them from the tip of each ``main`` branch):

.. code-block:: bash

   pip install -r requirements.txt

* `ocpy <https://github.com/ocean-colour/ocpy>`_ — data loaders, noise models,
  and ``Spectrum`` containers (the data side).
* `BING <https://github.com/ocean-colour/bing>`_ — the IOP retrieval engine
  (models, radiative transfer, fitting, evaluation).

Running the tests
-----------------------

The data-independent (Tier-1) test suite runs anywhere; data-dependent
(Tier-2) tests skip automatically when the ``$OS_COLOR`` data tree is absent:

.. code-block:: bash

   pytest -q
