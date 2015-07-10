***************************************
Working with AstrOmatic Codes and Files
***************************************

.. _installing_codes:

Installing Astromatic Software
==============================
It can be a bit of a hassle to install your first AstrOmatic code but once you've
successfully installed all of the dependent packages they all install pretty much
the same. I haven't done this in a while so this section is incomplete for now but
in the future this section should give instructions for installing all of the dependent
software as well as the astromatic codes for various operating systems.

.. _create_config:

Creating AstrOmatic Config Files
================================
For all of the AstrOmatic codes the default config file that the code uses can be displayed
by executing::

    sex -d

where in this case we used the SExtractor command (for other codes it would be ``scamp -d``, etc.).
There is also an extension of the default file that contains more advanced parameters that can be
displayed by executing::

    sex -dd

For SExtractor only, there is also a file that lists all of the possible output parameters
that the code can generate. This can be accessed by running::

    sex -dp

On a unix system (i.e. Linux or OS X) you can create a config file simply by typing::

    sex -dd > default.sex
    sex -dp > default.param
    scamp -dd > default.scamp
    swarp -dd > default.swarp
    psfex -dd > default.psfex

.. _using_fits_ldac:

FITS LDAC files
===============
SCAMP and PSFex require files in the FITS LDAC format to work. Currently this alternate
FITS format is not supported by astropy but it is likely that in the near future
:mod:`astromatic_wrapper.utils.ldac` will be integrated into the core astropy package
to make working with these files seemless. In the meantime :mod:`astromatic_wrapper.utils.ldac`
contains a set of functions that can be used to convert astropy tables to/from FITS LDAC
files.

FITS LDAC Format
----------------
The :func:`~astromatic_wrapper.utils.ldac.convert_hdu_to_ldac` is used to convert a
FITS binary table into the LDAC standard. The conversion used is based in a 
`this tex file <http://astrometry.net/svn/trunk/projects/scamp-integration/scamp-cats.tex>`_
by Dustin Lang. The main difference is that each table has a header written in a different
frame, so that if a catalog was made from a multi-extension FITS file with a primary header
and *X* frames, the FITS LDAC file will have *2X* frames, where frame *2n* is the FITS
LDAC frame corresponding to the frame *n* in the original image. See the afore mentioned
tex file for more.

Load a FITS LDAC file
---------------------

To load a FITS_LDAC file::

    >>> import astromatic_wrapper as aw
    >>> tbl = aw.utils.ldac.get_table_from_ldac('filename.fits', frame=1)

where a frame is required for a multi-extension FITS file that has multiple tables
(for example the output from SExtractor). The frame to specify should be the *actual*
frame of the table, *not* the frame in the FITS LDAC file.

Save or Convert a Table to FITS LDAC
------------------------------------
In some cases you might want to modify a table but save it as a FITS LDAC file that can
later be read into SCAMP or PSFex. To convert a table to a FITS LDAC hdulist use
:func:`~atromatic_wrapper.utils.ldac.convert_table_to_ldac` ::

    >>> hdulist = convert_table_to_ldac(tbl)
    >>> hdulist.write('filename.ldac.fits')

or use simply use :func:`~atromatic_wrapper.utils.ldac.save_table_as_ldac` ::

    >>> aw.utils.ldac.save_table_as_ldac(tbl, 'filename.fits')

SExtractor Tips
===============
Older versions of SExtractor used the notation ``sex filename.fits[1]`` would run SExtractor
on the second frame of the image, not the first (since filename.fits[0] is the
first image frame). This is not the case in the newest version '2.19.5', which you should
be using anyway.

SWarp Tips
==========
When working with cameras like DECam that have a large FOV I prefer to stack images
CCD by CCD instead of stacking the image as a whole like SExtractor does. In a 
soon to be released decam-tools package I have functions that implement this using
the astromatic-wrapper Pipeline. One important thing to remember about
this approch is that you *cannot* run SWarp on individual images to reproject them
and then run SWarp again to stack the images. When SWarp stacks a set of images
it requires them to have the same WCS constant parameters, meaning you should first
run SWarp on all of the iamges to reproject them to the same WCS, them SWarp on the
resampled CCD images to to stack them.