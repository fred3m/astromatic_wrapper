***********
Quick Start
***********

It is recommended that you have at least a cursory understanding of
`SExtractor <http://www.astromatic.net/software/sextractor>`_, it's parameters, and
how it works before starting; however this introduction might be sufficient to get
started. You will also need your own FITS image to work with, preferably one with multiple
extensions (CCD's).

.. _single_sextractor:

Running a Code on a Single Image
================================
In this example we will show how to run a single astromatic code outside on a single image.
Although we only demonstrate how to interface with SExtractor, the exact same proceedure
applies to all the AstrOmatic codes (with the exception of the configuration parameters).
To see an example of creating a pipeline that uses all of the SExtractor codes on a set of
images see :ref:`new_pipeline`.

SExtractor is an program that detects sources and performs photometry on astronomical
FITS images. The following example assumes that you have a fits file named 'my_img.fits'.

.. note::

    SExtractor does not work on compressed FITS files (fits.fz) so you will need to
    funpack the file before running SExtractor.

.. note::

    You must have `SExtractor <http://www.astromatic.net/software/sextractor>`_
    installed for this example to work.

First you need to import the astromatic_wrapper package and define your files::

    >>> import astromatic_wrapper as aw
    >>> files = {'image': 'my_img.fits'}

If you have a data quality mask or weight map you can also add them::

    >>> files['dqmask'] = 'my_img.dqmasl.fits'
    >>> files['wtmap'] = 'my_img.wtmap.fits'

Next you need to define the keyword arguments to run the code. At a minimum you must
supply the name of the code you are using. To see a dictionary of all the available codes
and their command line name enter::

    >>> aw.api.codes
    {'SExtractor': 'sex', 'SWarp': 'swarp', 'PSFEx': 'psfex', 'SCAMP': 'scamp'}

In this case we use::

    >>> kwargs = {'code': 'SExtractor'}

If you are running an AstrOmatic code that is not a system wide install, you can change the
command used to execute the code by setting::

    >>> kwargs['cmd'] = 'different/path/to/sex'

All AstrOmatic codes use config files containing input parameters whose filenames conventionally
end with an extension that is the same as command name (for example config.sex for SExtractor,
config.scamp for SCAMP, etc.). For this example we won't specify a config file so that 
SExtractor will just use its internal default. If we have our own config file we can 
instruct SExtractor (or any other astromatic code) to use it by entering::

    >>> kwargs['config_file'] = 'config.sex'

It can be useful to change certain parameters in a config
file so SExtractor allows the user to pass command line arguments using the 'config' key,
for example we may want to change the name of the output catalog::

    >>> kwargs['config']={'CATALOG_NAME':'test.ldac.fits'}

An anomally of the AstrOmatic codes is that they like input catalogs in the form of the
FITS LDAC standard, which is slightly different than standard FITS tables. Astromatic-Wrapper
provides an I/O scheme to interface with FITS LDAC files in the :ref:`using_fits_ldac`.
To change the output type to FITS LDAC from the default ('ASCII_HEAD') we use::

    >>> kwargs['config']['CATALOG_TYPE'] = 'FITS_LADC'

In this quick example we will not use a filter to assist SExtractor in finding sources so
we set::

    >>> kwargs['config']['FILTER'] = 'N'

One feature that is unique to SExtractor (as opposed to the other AstrOmatic codes) is that
it also requires a parameters file to set the output of the code. If you already have a
parameters file you can tell SExtractor to use it with::

    >>> kwargs['config']['PARAMETERS_NAME'] = 'filename.param'

otherwise you must specify a 'temp_path' and the names of the parameters you want
SExtractor to export::

    >>> kwargs['temp_path'] = '.'
    >>> kwargs['params'] = ['NUMBER', 'EXT_NUMBER', 'XWIN_WORLD', 'YWIN_WORLD', 'MAG_AUTO']

To create an :class:`.Astromatic` object that will run the code we type

    >>> sextractor = aw.api.Astromatic(**kwargs)

To run sextractor on a single frame::

    >>> sextractor.run_frames(files['image'], frames=[1]) # doctest: +SKIP
    > WARNING: default.sex not found, using internal defaults

    ----- SExtractor 2.19.5 started on 2015-07-08 at 15:46:12 with 1 thread

    ----- Measuring from: c4d_150528_065922_ooi_r_v1.fits [1/60]
          "Unnamed" / no ext. header / 2046x4094 / 32 bits (floats)
    (M+D) Background: 25.3315    RMS: 3.28377    / Threshold: 4.92565    
          Objects: detected 12304    / sextracted 8595            

    > All done (in 5.1 s: 803.3 lines/s , 1686.4 detections/s)

.. note::

    Only SExtractor and SWarp run on individual frames. PSFex and SCAMP run on the entire
    catalog that was passed to them.

To run SExtractor on an entire image::

    >>> sextractor.run(files['image']) # doctest: +SKIP
    (output suppressed)

.. note::

    It is also possible to first create the :class:`.Astromatic` class using
    ``sextractor = aw.api.Astromatic('SExtractor')`` and then pass the configuration
    parameters to the run command ``sextractor.run(files['image'], **kwargs)`` or 
    ``sextractor.run_frames(files['image'], frames=[1], **kwargs)``. It is also possible
    to use ``sextractor = aw.api.Astromatic(**kwargs)`` and 
    ``sextractor.run(files['image'], **new_kwargs)``, in which case the new_kwargs in the
    run method take precedent over the kwargs set when the class was initialized.

Putting it all together we have::

    import astromatic_wrapper as aw

    files = {
        'image': 'my_img.fits',
        'dqmask': 'my_img.dqmask.fits',
        'wtmap': 'my_img.wt_map.fits'
    }
    kwargs = {
        'code': 'SExtractor',
        #'cmd': 'different/path/to/sex',
        'config': {
            'CATALOG_NAME': 'test.ldac.fits',
            'CATALOG_TYPE': 'FITS_LDAC',
            'FILTER': 'N',
        },
        'temp_path': '.',
        'params': ['NUMBER', 'EXT_NUMBER', 'XWIN_WORLD', 'YWIN_WORLD', 'MAG_AUTO'],
        #'config_file': 'config.sex'
    }
    
    sextractor = aw.api.Astromatic(**kwargs)
    sextractor.run_frames(files['image'], frames=[1])
    #sextractor.run(files['image'])

Now we can open the data as an astropy table using::

    >>> catalog = aw.utils.ldac.get_table_from_ldac('test.ldac.fits') # doctest: +SKIP
    >>> catalog # doctest: +SKIP
    NUMBER EXT_NUMBER   XWIN_WORLD    YWIN_WORLD   MAG_AUTO
                           deg           deg         mag   
    ------ ---------- ------------- -------------- --------
         1          1  275.80827774 -50.0434433783 -12.1171
         2          1 275.798937295 -50.0183562274 -5.31479
         3          1 275.794967779 -50.0183230473 -7.09294
         4          1 275.792679237 -50.0184461957 -8.99806
         5          1 275.802384111  -50.148179237 -14.6061
         6          1 275.799356843 -50.0689823418 -13.5756
         7          1 275.799459347  -50.020292202 -7.62385
         8          1 275.797433239 -50.1242247153 -13.0597
         9          1 275.795337901 -50.1232484108 -9.93003
        10          1 275.796363189 -50.0510042866 -9.32829
       ...        ...           ...            ...      ...
      8586          1 276.207597916 -50.0754202482 -3.82954
      8587          1 276.193157798 -50.0811452427 -5.45954
      8588          1  276.24091269 -50.0409055391 -10.7668
      8589          1 276.236753962 -50.0533390955 -6.89498
      8590          1 276.236856181 -50.0440666735 -4.34284
      8591          1 276.244645469 -50.1200226072 -8.52295
      8592          1 276.221681288 -50.1324512891 -6.54179
      8593          1 276.192358853 -50.1377186626 -14.3937
      8594          1 276.206296663 -50.1512013966  -7.4894
      8595          1 276.206454781 -50.0597536065 -11.7223
    Length = 8595 rows