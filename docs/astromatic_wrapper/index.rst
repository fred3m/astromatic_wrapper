******************
AstrOmatic Wrapper
******************

Astromatic-Wrapper is a package for running python pipelines that depend on 
the `Astromatic Software Suite`_. The package mainly consists of an API to 
allow the user to run AstrOmatic codes such as `SExtractor`_, `SCAMP`_, `SWarp`_, 
`PSFEx`_, etc. from python scripts that make it easy to modify the configuration
files and parameters used.

It also contains a Pipeline class for building custom pipelines that include
AstrOmatic codes that can be used to process large datasets.


Reference/API
=============

.. automodapi:: astromatic_wrapper

.. _Astromatic Software Suite: http://www.astromatic.net/

.. _SExtractor: http://www.astromatic.net/software/sextractor

.. _SCAMP: http://www.astromatic.net/software/scamp

.. _SWarp: http://www.astromatic.net/software/swarp

.. _PSFEx: http://www.astromatic.net/software/psfex