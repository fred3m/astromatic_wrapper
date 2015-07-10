********
Overview
********

Astromatic-Wrapper is a python wrapper for Emmanuel Bertin's `AstrOmatic <www.astromatic.net>`_
software suite, incuding SExtractor, SCAMP, SWarp, and PSFex. While tools like SExtractor
are extraordinarily useful for both their accuracy and speed, because they are command line
applications that read their settings from local config files it can be a chore to implement
them in a pipeline for reducing large volumes of data, especially in the initial stages of
exploring a new set of images. This has led a multitue of astronomers to create their own
wrappers for SExtractor and its companions, usually in python or shell script.

Why another wrapper for AstrOmatic Software?
============================================
While there are a number of open source astromatic wrappers already they often treat each 
code differently, requiring an entirely different API to interact with each code. One of the
many things that Bertin has done extremely well is to standardize his API so that a single class
can easily be written to call any AstrOmatic code the user wishes, which we call the
:class:`.Astromatic` class.

The other feature that is unique to this package is the :class:`.Pipeline` class, designed
to aid users in creating pipelines to automatically reduce large volumes of images. If a user
simply wants to run SExtractor or SCAMP on a single image there is no need for a pipeline
of any kind, running them from the command line works just fine. The :class:`.Pipeline` class
allows the user to build a pipeline step by step and then execute
any subset of the steps as desired. After each step is executed a copy of the pipeline is saved
using the `dill <https://github.com/uqfoundation/dill>`_ module so that if the pipeline
crashes for any reason, it can be restarted where it left off (possibly with changes to its
parameters to prevent it from crashing again). The pipeline automatically instructs the 
AstrOmatic codes to build XML log files and links them to the pipeline log so that there is a 
record of each step taken.

Finally, AstrOmatic codes use an outdated file format FITS_LDAC that doesn not conform to 
the official FITS standard and the XML output VOTables also do not all conform to the votable
standard. Astromatic_Wrapper contains functions to convert FITS_LDAC files to astropy
tables and vice versa, as well as mask votable fields that do not match the standard. It's
little things like these that I hope will save other astronomers the time I had to put in 
to write them myself.