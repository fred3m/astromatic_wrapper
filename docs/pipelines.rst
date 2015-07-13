.. _new_pipeline:

*********
Pipelines
*********
Astromatic-Wrapper is much more useful for users who wish to build a pipeline to
run AstrOmatic software on a large set of images. The :class:`.Pipeline` class allows
users to create a custom pipeline that can be logged and saved for future use and
reference.

I've found it most useful to use `Jupyter <https://jupyter.org/>`_ (formerly IPython)
while running pipelines because inevitably something crashes along the way and while
the pipeline is designed to be loaded from a log file when it crashes, it's much
easier to diagnose a problem and work with it in Jupyter.

Incuded in the 'examples' directory are sample Jupyter notebooks (iPython version 3) 
that give sample code to work with Pipelines.

.. _pipeline_setup:

Setting up the Pipeline: Best Practices and Useful Tips
=======================================================

To assist in organizing your files, :py::class:`.Pipeline`'s accept a ``paths`` dictionary
that lists where to store various file types. When the pipeline is created, the user will
be prompted to create any paths that do not exist in the systems file directory (or
optionally, they can automatically be created without prompting the user). At a minimum 
``paths`` should contain a 'temp' key, which tells the pipeline where to store temporary files. 
It is also recommended to use a 'log' key, which will automatically instructs each AstrOmatic 
code run to generate an XML output file with information about the parameters used and any 
errors and warnings generated in its execution. I use the 'temp' path to store all of the 
intermediate catalogs and images the software creates but I usually create 'catalogs' and 
'stacks' directories to store the end products of the pipeline, and an 'images' keyword 
to point to the path where my images are stored.

I also commonly put all of my config files 
in a single 'config' directory. This tutorial assumes that you have created config files 
for all of the codes used (see :ref:`create_config` for instructions on creating config files).

You can also add any keyword arguments that you wish when you initialize your pipeline.
For example, if you're running the pipeline on a cluster, you may have had to install the 
AstrOmatic software in a local directory (as opposed to a system wide installation). The optional
``built_paths`` argument tells the code which command to use when executing each
code.

The code to setup our pipeline should look something like::

    import os
    import datetime
    import astromatic_wrapper as aw
    
    # Get the current date and time to 
    log_path = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S_test')
    
    # Set defaults
    base_path = '/Users/me/dataset1'
    paths = {
        'temp': os.path.join(base_path, 'temp'),
        'log': os.path.join(base_path, 'log', log_path),
        'config': os.path.join(base_path, 'config'),
        'catalogs': os.path.join(base_path, 'catalogs),
        'stacks': os.path.join(base_path. 'stacks'),
        'images': '/Users/me/images'
    }
    
    # If you are using a system wide install you can remove the following code
    # that specifies build_paths for each code
    build_path = '/Users/me/astromatic/build'
    build_paths = {
        'SExtractor': os.path.join(build_path, 'sex', 'bin', 'sex'),
        'SCAMP': os.path.join(build_path, 'scamp', 'bin', 'scamp'),
        'SWARP': os.path.join(build_path, 'swarp', 'bin', 'swarp'),
        'PSFEx': os.path.join(build_path, 'psfex', 'bin', 'psfex')
    }
    # Create the pipeline
    pipeline = astromatic.utils.pipeline.Pipeline(paths, build_paths=build_paths)

Building a Pipeline
===================
Once you have created your pipeline it's time to add steps.
The :func:`~astromatic_wrapper.Pipeline.add_step` method adds a new
:class:`.PipelineStep` to ``Pipeline.steps``, a list that contains all of the
steps in a pipeline. 

Functions
---------
:func:`~astromatic_wrapper.Pipeline.add_step` requires
a 'func' argument, the function to be executed (this does not have to be a function
to run an Astromatic code but can be any python function). When you run the pipeline the
code expects the function to return a dictionary with a 'status' key that is either
'success' or 'error'. If anything else is returned the status of the step will be
set to 'unknown' in the pipeline log.

Tags
----
You can also specify any 'tags' to associate with the step, for example in the 
future you may only want to run a subset of the pipeline so if you add a list of tags
to each step it will be easier to select only the desired steps (see :ref:`run_subset`
for more).

Ignoring Errors and Exceptions
------------------------------
If the 'status' key in the function result is 'error', by default the pipeline will cease
execution and a :class:`PipelineError` will occur. If ``ignore_errors=True`` is passed to the
:func:`~astromatic_wrapper.Pipeline.add_step` function the pipeline will log the
error, warn the user, and continue execution.

Similarly, by default if there is an Exception raised in the function the pipeline will
terminate and a :class:`PipelineError` will occur. If ``ignore_exceptions=True`` is passd to the
:func:`~astromatic_wrapper.Pipeline.add_step` function the pipeline will log the
error, warn the user, and continue execution.

Function Arguments
------------------
All other keyword arguments passed to :func:`~astromatic_wrapper.Pipeline.add_step` will
become keyword arguments for 'func', the function that will run in the pipeline.

Simple Example
--------------
This section shows how to add a single step to the pipeline that runs SExtractor,
similar to the :ref:`single_sextractor` example. This assumes that you have already
entered the code from :ref:`pipeline_setup` above. ::

    import os
    import astromatic_wrapper as aw
    # Change these to your file paths and names
    files = {
        'image': 'my_img.fits',
        'dqmask': 'my_img.dqmask.fits',
        'wtmap': 'my_img.wt_map.fits'
    }
    # Name of the output path
    catalog_name = os.path.join(pipeline.paths['catalogs'], 
        os.path.basename(files['image']).replace('.fits', '.ldac.fits')))
    kwargs = {
        # image to SExtract
        'files': files['image'],
        # Arguments to initialize Astromatic class
        'api_kwargs': { 
            # Configuration parameters
            'config': {
                'CATALOG_NAME': catalog_name,
                'CATALOG_TYPE': 'FITS_LDAC',
                'FILTER': False,
                'WEIGHT_TYPE': 'MAP_WEIGHT',
            },
            # config file to use (instead of SExtractor internal defaults)
            'config_file': os.path.join(pipeline.config_path, 'default.sex')
        },
        # Output parameters
        'params': ['NUMBER', 'EXT_NUMBER', 'XWIN_IMAGE', 'YWIN_IMAGE', 'ERRAWIN_IMAGE',
            'ERRBWIN_IMAGE', 'ERRTHETAWIN_IMAGE', 'XWIN_WORLD', 'YWIN_WORLD', 'FLUX_APER', 
            'FLUXERR_APER', 'IMAFLAGS_ISO', 'FLAGS', 'FLAGS_WEIGHT', 'FLUX_RADIUS',
            'ELONGATION'],
        # Frames to run SExtractor on
        'frames': frames
    }
    # Add the step to the pipeline
    pipeline.add_step(aw.api.run_sex, ['step1', 'SExtractor'], **kwargs)

Now you can run the step with::

    >>> pipeline.run()
    > WARNING: default.sex not found, using internal defaults

    ----- SExtractor 2.19.5 started on 2015-07-08 at 15:46:12 with 1 thread

    ----- Measuring from: c4d_150528_065922_ooi_r_v1.fits [1/60]
          "Unnamed" / no ext. header / 2046x4094 / 32 bits (floats)
    (M+D) Background: 25.3315    RMS: 3.28377    / Threshold: 4.92565    
          Objects: detected 12304    / sextracted 8595            

    > All done (in 5.1 s: 803.3 lines/s , 1686.4 detections/s)

For more on running a Pipeline see :ref:`running_a_pipeline`.

.. _full_pipeline_example:

Full Example
------------
The following block of code creates a function that will add a series of steps to the
pipeline defined in :ref:`pipeline_setup`. Depending on the images you are using some
of the parameters may need to be changed or ommitted and this is by no means a
final product, but it should give you a basic idea about how to build your own pipeline.::

    def build_pipeline(pipeline, exposures, ref_catalog='2MASS', ref_band='DEFAULT', frames=[],
            stack_name = 'test_stack.fits', output_cat_name='test_psf.ldac.fits'):
        # Generate catalogs from sextractor
        catalog_names = []
        for files in exposures:
            # Create names for the output catalogs for each image
            catalog_names.append(os.path.join(pipeline.paths['temp'], 
                os.path.basename(files['image']).replace('.fits', '.cat')))
            kwargs = {
                # image to SExtract
                'files': files,
                # Arguments to initialize Astromatic class
                'api_kwargs': { 
                    # Configuration parameters
                    'config': {
                        'CATALOG_NAME': catalog_names[-1],
                        'CATALOG_TYPE': 'FITS_LDAC',
                        'FILTER': False,
                        'WEIGHT_TYPE': 'MAP_WEIGHT',
                    },
                    # Output parameters
                    'params': ['NUMBER', 'EXT_NUMBER', 'XWIN_IMAGE', 'YWIN_IMAGE', 'ERRAWIN_IMAGE',
                        'ERRBWIN_IMAGE', 'ERRTHETAWIN_IMAGE', 'XWIN_WORLD', 'YWIN_WORLD', 'FLUX_AUTO', 
                        'FLUXERR_AUTO', 'IMAFLAGS_ISO', 'FLAGS', 'FLAGS_WEIGHT', 'FLUX_RADIUS',
                        'ELONGATION'],
                },
                # Frames to run SExtractor on
                'frames': frames
            }
            # Add the step to the pipeline
            pipeline.add_step(aw.api.run_sex, ['step1', 'SExtractor'], **kwargs)

        # Get astrometric solution from SCAMP
        # Use SCAMP to get astrometric solutions
        kwargs = {
            'catalogs': catalog_names,
            'api_kwargs': {
                'config': {
                    'ASTREF_CATALOG': ref_catalog,
                    'ASTREF_BAND': ref_band,
                    'SOLVE_PHOTOM': 'N',
                    'CHECKPLOT_DEV': 'NULL'
                },
            }
        }
        pipeline.add_step(aw.api.run_scamp, ['step2', 'SCAMP'],**kwargs)
    
        # Resample (rotate and scale) and combine (stack) images
        stack_filename = os.path.join(pipeline.paths['temp'], stack_name)
        kwargs = {
            'filenames': [exp['image'] for exp in exposures],
            'api_kwargs': {
                'config': {
                    'WEIGHT_TYPE': 'MAP_WEIGHT',
                    'WEIGHT_SUFFIX': '.wtmap.fits',
                    'IMAGEOUT_NAME': stack_filename,
                    'WEIGHTOUT_NAME': stack_filename.replace('.fits','.wtmap.fits'),
                },
            },
            'frames': frames
        }
        pipeline.add_step(aw.api.run_swarp, ['step3', 'SWarp'], **kwargs)
    
        # Get positions in stack for PSF photometry
        kwargs = {
            'files': {
                'image': stack_filename,
                'wtmap': stack_filename.replace('.fits', '.wtmap.fits')
            },
            'api_kwargs': {
                'config': {
                    'CATALOG_TYPE': 'FITS_LDAC',
                    'FILTER': False,
                    'WEIGHT_TYPE': 'MAP_WEIGHT',
                },
                'params': ['NUMBER', 'EXT_NUMBER', 'XWIN_IMAGE', 'YWIN_IMAGE', 'ERRAWIN_IMAGE',
                    'ERRBWIN_IMAGE', 'ERRTHETAWIN_IMAGE', 'XWIN_WORLD', 'YWIN_WORLD', 'FLUX_APER(1)', 
                    'FLUXERR_APER(1)', 'FLAGS', 'FLAGS_WEIGHT', 'FLUX_RADIUS',
                    'ELONGATION', 'VIGNET(20,20)', 'SNR_WIN'],
            },
            'frames': frames
        }
        pipeline.add_step(aw.api.run_sex, ['step4', 'SExtractor'], **kwargs)
    
        # Calculate PSF
        kwargs = {
            'catalogs': stack_filename.replace('.fits', '.cat'),
            'api_kwargs': {
                'config': {
                    'CENTER_KEYS': 'XWIN_IMAGE,YWIN_IMAGE',
                    'PSFVAR_KEYS': 'XWIN_IMAGE,YWIN_IMAGE',
                    'CHECKPLOT_DEV': 'NULL',
                    'PSF_SUFFIX': '.psf'
                },
            }
        }
        pipeline.add_step(aw.api.run_psfex, ['step5', 'PSFEx'], **kwargs)
    
        # Calculate PSF photometry for stacked image
        # Get positions in stack for PSF photometry
        catalog_name = os.path.join(pipeline.paths['catalogs'], output_cat_name)
        kwargs = {
            'files': {
                'image': stack_filename,
                'wtmap': stack_filename.replace('.fits', '.wtmap.fits')
            },
            'api_kwargs': {
                'config': {
                    'PSF_NAME': os.path.join(stack_filename.replace('.fits', '.psf')),
                    'CATALOG_TYPE': 'FITS_LDAC',
                    'FILTER': False,
                    'CATALOG_NAME': catalog_name,
                    'WEIGHT_TYPE': 'MAP_WEIGHT',
                },
                'params': ['NUMBER', 'EXT_NUMBER', 'XWIN_IMAGE', 'YWIN_IMAGE', 'ERRAWIN_IMAGE',
                    'ERRBWIN_IMAGE', 'ERRTHETAWIN_IMAGE', 'XWIN_WORLD', 'YWIN_WORLD', 'FLUX_AUTO', 
                    'FLUXERR_AUTO', 'FLAGS', 'FLAGS_WEIGHT', 'FLUX_RADIUS',
                    'ELONGATION', 'MAG_AUTO', 'MAGERR_AUTO', 'ALPHAPSF_SKY', 'DELTAPSF_SKY',
                    'ERRX2PSF_WORLD','ERRY2PSF_WORLD', 'FLUX_PSF', 'FLUXERR_PSF', 'MAG_PSF', 'MAGERR_PSF'],
            },
            'frames': frames
        }
        pipeline.add_step(aw.api.run_sex, ['step6', 'SExtractor'], **kwargs)
    
        def save_output(pipeline, old_stack, new_stack, old_cat, new_cat):
            # Copy the final stack and catalog from the temp folder
            import shutil
            # Move the weight map if it exists
            if os.path.isfile(old_stack.replace('.fits', '.wtmap.fits')):
                shutil.move(old_stack.replace('.fits', '.wtmap.fits'), new_stack.replace('.fits', '.wtmap.fits'))
            shutil.move(old_stack, new_stack)
            shutil.move(old_cat, new_cat)
            result = {
                'status': 'success'
            }
            return result
    
        kwargs = {
            'old_stack': stack_filename,
            'new_stack': os.path.join(pipeline.paths['stacks'], stack_name),
            'old_cat': catalog_name, 
            'new_cat': os.path.join(pipeline.paths['catalogs'], output_cat_name)
        }
        pipeline.add_step(save_output, ['step7', 'save_output'], **kwargs)
    
        return pipeline

Once we have designed our pipeline it is time to build it for a set of images. In this example
we have three different exposures with data quality masks and weight maps of the same field,
and we will only only run the pipeline on the first frame. ::

    exposures = [
        {
            'image': os.path.join(pipeline.paths['images'], '206401.fits'),
            'dqmask': os.path.join(pipeline.paths['images'], '206401.dqmask.fits'),
            'wtmap': os.path.join(pipeline.paths['images'], '206401.wtmap.fits'),
        },
        {
            'image': os.path.join(pipeline.paths['images'], '206402.fits'),
            'dqmask': os.path.join(pipeline.paths['images'], '206402.dqmask.fits'),
            'wtmap': os.path.join(pipeline.paths['images'], '206402.wtmap.fits'),
        },
        {
            'image': os.path.join(pipeline.paths['images'], '206403.fits'),
            'dqmask': os.path.join(pipeline.paths['images'], '206403.dqmask.fits'),
            'wtmap': os.path.join(pipeline.paths['images'], '206403.wtmap.fits'),
        }
    ]
    frames = [1]
    
    pipeline = build_pipeline(pipeline, exposures=exposures, frames=frames)

.. note::

    This pipeline will only run on a single frame *n* (``frames=[n]``) or the
    entire image (``frames=[]``). Trying to run on multiple frames (``frames=[1,2]``)
    will cause this particular example pipeline to crash.

.. _running_a_pipeline:

Running a Pipeline
==================

Running the Entire Pipeline
---------------------------
To run all of the steps in a Pipeline in order simply type::

    >>> pipeline.run()

.. _run_subset:

Running a subset of the Pipeline
--------------------------------
It may be desirable to run subsets of a Pipeline, for example testing the code or 
fixing a function kwarg that crashed a pipeline. There are several ways to run a
subset discussed in the following sections.

Automatic Selection of Steps
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In :ref:`full_pipeline_example` above each step was given a set of tags in the form of
``[step_name, code_name]``, for example the first three steps had the tag 
``['step1', 'SExtractor]``. To run only those steps run::

    >>> pipeline.run(['step1'])

or

    >>> pipeline.run(run_tags=['step1])

which will only run the first three steps which detect sources in the given images.

Instead of specifying tags to run, you might also want to specify tags not to run, for example
maybe you want to skip the last step that saves the files to a new directory::

    >>> pipeline.run(ignore_tags=['step7'])

which will run every step except the last.

If both 'run_tags' and 'ignore_tags' are given, ignore tags take precedence, meaning a
step that has a tag from 'run_tags' and a tag from 'ignore_tags' will not be run but
any steps that have 'run_tags' and not 'ignore_tags' will be run.

Custom Selection of Steps
^^^^^^^^^^^^^^^^^^^^^^^^^
Sometimes the simplistic selection of tags may not be sufficient and you may want to
customize the subset of steps that you will run. In this case you can generate a list
of steps yourself, for example::

    >>> steps = [step for step in pipeline.steps if 'SExtractor' in step.tags and '206401.fits' == step.func_kwargs['files']['image']]

Which really just selects the step that ran SExtractor on the image '206401.fits' 
(of course this is not the best way to run SExtractor on a single image).

Then to run the chosen steps in the pipeline:

    >>> pipeline.run(run_steps=steps)

Editing a Step
--------------
Sometimes it's useful to edit a step inthe pipeline, for example you may be halfway through
a run when the code breaks because of a syntax error. Perhaps we chose the wrong image names
when we setup our pipeline and '206403.fits' should have been '206400.fits'. The pipeline
may have successfully run on the first two images but then crashed when it got to the third.

The pipeline keeps two different lists of steps: ``Pipeline.steps`` is a list
of all the steps added to a Pipeline, ``Pipeline.run_steps`` is the subset
of ``Pipeline.steps`` that are scheduled to be run (or have been run already).
The index of the current step is ``Pipeline.run_step_idx`` so that 
``Pipeline.run_steps[run_step_idx]`` is the next step scheduled to run, or in the
case of a broken Pipeline, the step that threw the error.

To change the filename in ``Pipeline.steps`` we use::

    >>> idx = pipeline.run_steps[pipeline.run_step_idx]
    >>> pipeline.steps[idx].func_kwargs['api_kwargs']['files'] = {'image': '206400.fits'}

and see that this changed the run step::

    >>> pipeline.run_steps[pipeline.run_step_idx].func_kwargs['api_kwargs']['files']['image']
    206400.fits

.. _resume_pipeline:

Resuming a Pipeline
-------------------
Once we have made changes to a step or fixed whatever connectivity or file I/O error
caused our pipeline to break, we are ready to resume our pipeline. To simply pickup at the
same step we left off in we can run::

    >>> pipeline.run(resume=True)

If instead we need to skip a step (for whatever reason) we can specify the step to start on

    >>> pipeline.run(resume=True, start_idx=5)

.. _warning::

    In order to specify a start index you also need to set ``resume=True`` if you
    are using a subset of pipeline.steps, otherwise the pipeline will reset 
    ``pipeline.run_steps`` and start from ``start_idx``.

In some instances you may have completely lost contact with the server, or run a pipeline
from a python script instead of Jupyter (iPython). To see how to load an automatically
saved instance of a pipeline see :ref:`pipeline_logging`

.. _pipeline_logging:

Logging and Loading a Pipeline
------------------------------
Several different log files may be created in the execution of a Pipeline. All of the 
Astromatic codes have the ability to export an XML file that contains information about
the parameters used to run the code, any errors or warnings that occured, and in
some cases a list of results. If the pipeline was initialized with a 'log' keyword
in 'paths', this will automatically be done by the pipeline when an astromatic
function from :mod:`astromatic_wrapper.api` is run.

The Pipeline itself is also saved in the log directory (if it was specified upon
initialization) using the `dill <https://pypi.python.org/pypi/dill/0.2.3>`_
serialization package. This allows you to load the pipeline in the exact state it was
in before running the step that caused it to crash. To load a saved pipeline::

    >>> import dill
    >>> pipeline=dill.load('/path/to/log/pipeline.p')

where `/path/to/log` is the directory ``pipeline.paths['log']``. Then just
follow the steps in :ref:`resume_pipeline` to continue, for example::

    >>> pipeline.run(resume=True)