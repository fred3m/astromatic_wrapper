import os
import pandas
import numpy as np
from sqlalchemy import create_engine
import subprocess
import copy
from collections import OrderedDict
import logging
from six import string_types
import datetime
from astropy.io import fits

from toyz.utils.errors import ToyzError
from astrotoyz.astromatic import api
import decamtoyz.utils as utils

logger = logging.getLogger('decamtoyz.pipeline')

class PipelineError(ToyzError):
    pass

class Pipeline:
    def __init__(self, img_path, idx_connect_str, temp_path, cat_path, 
            result_path=None, resamp_path=None, stack_path=None,
            config_path=None, build_paths={}, log_path=None, create_idx = None,
            default_kwargs={}, steps=[], pipeline_name=None):
        """
        Parameters
        ----------
        img_path: str
            path to decam images
        idx_connect_str: str
            sqlalchemy connection string to decam index database
        temp_path: str
            path to store temporary files
        cat_path: str
            path to save final catalogs
        result_path: str
            path to save resampled and stacked images
        config_path: str
            path to check for astromatic config files
                * defaults to decamtoyz/defaults
        build_paths: dict
            paths to astromatic builds
                * Not needed if the codes were installed system wide (ex. 'sex' runs SExtractor)
                * Keys are commands for astromatic packages ('sex', 'scamp', 'swarp', 'psfex')
                * Values are the paths to the build for the given key
        log_path: str
            path to save astromatic xml log files
        create_idx: bool
            By default, if the decam index DB cannot be found, the user will
            be prompted to create the index. Setting `create_idx` to `True` overrides 
            this behavior and automatically creates the index. Setting `create_idx` ``False``
            will raise an error
        """
        if idx_connect_str.startswith('sqlite'):
            if not os.path.isfile(idx_connect_str[10:]):
                logger.info('path', idx_connect_str[10:])
                if create_idx is not None:
                    if create_idx:
                        import toyz.utils.core as core
                        if not core.get_bool(
                                "DECam file index does not exist, create it now? ('y'/'n')"):
                            raise PipelineError("Unable to locate DECam file index")
                    else:
                         raise PipelineError("Unable to locate DECam file index")
                import decamtoyz.index as index
                import toyz.utils.core as core
                recursive = core.get_bool("Search '{0}' recursively for images? ('y'/'n')")
                index.build_idx(img_path, idx_connect_str, True, recursive, True)
        self.idx = create_engine(idx_connect_str)
        self.idx_connect_str = idx_connect_str
        self.img_path = img_path
        self.temp_path = temp_path
        self.cat_path = cat_path
        self.result_path = result_path
        self.resamp_path = resamp_path
        self.stack_path = stack_path
        self.build_paths = build_paths
        self.default_kwargs = default_kwargs
        # IF the user doesn't specify a path for config files, use the default decam config files
        if config_path is None:
            from decam import root
            self.config_path = os.path.join(root, 'default')
        else:
            self.config_path = config_path
        
        # If any of the specified paths don't exist, give the user the option to create them
        utils.check_path('temp_path', self.temp_path)
        utils.check_path('cat_path', self.cat_path)
        utils.check_path('stack_path', self.stack_path)
        
        # If the user specified a set of steps for the pipeline, add them here
        self.steps = steps
        self.next_id = 0
        
        # Set the time that the pipeline was created and create a directory
        # for log files
        self.name = pipeline_name
        self.run_date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.log_path = os.path.join(self.log_path, self.run_date)
        if pipeline_name is not None:
            self.log_path += '_'+pipeline_name
        import toyz.utils.core as core
        core.create_paths([self.log_path])
    
    def run_sex(self, step_id, files, api_kwargs={}, frames=None):
        """
        Run SExtractor with a specified set of parameters.
        
        Parameters
        ----------
        step_id: str
            Unique identifier for the current step in the pipeline
        files: dict
            Dict of filenames for fits files to use in sextractor. Possible keys are:
                * image: filename of the fits image (required)
                * dqmask: filename of a bad mixel mask for the given image (optional)
                * wtmap: filename of a weight map for the given image (optional)
        kwargs: dict
            Keyword arguements to pass to ``atrotoyz.Astromatic.run`` or
            ``astrotoyz.Astromatic.run_sex_frames``
        frames: str (optional)
            Only run sextractor on a specific set of frames. This should either be an 
            integer string, or a string of csv's
        
        Returns
        -------
        result: dict
            Result of the astromatic code execution. This will minimally contain a ``status``
            key, that indicates ``success`` or ``error``. Additional keys:
            - error_msg: str
                If there is an error and the user is storing the output or exporting XML metadata,
                ``error_msg`` will contain the error message generated by the code
            - output: str
                If ``store_output==True`` the output of the program execution is
                stored in the ``output`` value.
            - warnings: str
                If the WRITE_XML parameter is ``True`` then a table of warnings detected
                in the code is returned
        """
        if 'code' not in api_kwargs:
            api_kwargs['code'] = 'SExtractor'
        if 'cmd' not in api_kwargs and 'SExtractor' in self.build_paths:
            api_kwargs['cmd'] = self.build_paths['SExtractor']
        if 'temp_path' not in api_kwargs:
            api_kwargs['temp_path'] = self.temp_path
        if 'config' not in api_kwargs:
            api_kwargs['config'] = {}
        if 'CATALOG_NAME' not in api_kwargs['config']:
            api_kwargs['config']['CATALOG_NAME'] = files['image'].replace('.fits', '.cat')
        if 'FLAG_IMAGE' not in api_kwargs['config'] and 'dqmask' in files:
            api_kwargs['config']['FLAG_IMAGE'] = files['dqmask']
        if 'WEIGHT_IMAGE' not in api_kwargs['config'] and 'wtmap' in files:
            api_kwargs['config']['WEIGHT_IMAGE'] = files['wtmap']
        if 'WRITE_XML' not in api_kwargs['config']:
            api_kwargs['config']['WRITE_XML'] = 'Y'
        if 'XML_NAME' not in api_kwargs['config']:
            api_kwargs['config']['XML_NAME'] = os.path.join(pipeline.log_path, 
                '{0}.sex.log.xml'.format(step_id))
        sex = api.Astromatic(**api_kwargs)
        if frames is None:
            result = sex.run(files['image'])
        else:
            result = sex.run_frames(files['image'], 'SExtractor', frames, False)
        return result
    
    def run_scamp(self, step_id, catalogs, api_kwargs={}, save_catalog=None):
        """
        Run SCAMP with a specified set of parameters
        
        Parameters
        ----------
        step_id: str
            Unique identifier for the current step in the pipeline
        catalogs: list
            List of catalog names used to generate astrometric solution
        api_kwargs: dict
            Dictionary of keyword arguments used to run SCAMP
        save_catalog: str (optional)
            If ``save_catalog`` is specified, the reference catalog used to generate the
            solution will be save to the path ``save_catalog``.
        
        Returns
        -------
        result: dict
            Result of the astromatic code execution. This will minimally contain a ``status``
            key, that indicates ``success`` or ``error``. Additional keys:
            - error_msg: str
                If there is an error and the user is storing the output or exporting XML metadata,
                ``error_msg`` will contain the error message generated by the code
            - output: str
                If ``store_output==True`` the output of the program execution is
                stored in the ``output`` value.
            - warnings: str
                If the WRITE_XML parameter is ``True`` then a table of warnings detected
                in the code is returned
        """
        if 'code' not in api_kwargs:
            api_kwargs['code'] = 'SCAMP'
        if 'cmd' not in api_kwargs and 'SCAMP' in self.build_paths:
            api_kwargs['cmd'] = self.build_paths['SCAMP']
        if 'temp_path' not in api_kwargs:
            api_kwargs['temp_path'] = self.temp_path
        if 'config' not in api_kwargs:
            api_kwargs['config'] = {}
        if save_catalog is not None:
            api_kwargs['config']['SAVE_REFCATALOG'] = 'Y'
            api_kwargs['config']['REFOUT_CATPATH'] = save_catalog
        if 'WRITE_XML' not in api_kwargs['config']:
            api_kwargs['config']['WRITE_XML'] = 'Y'
        if 'XML_NAME' not in api_kwargs['config']:
            api_kwargs['config']['XML_NAME'] = os.path.join(pipeline.log_path, 
                '{0}.scamp.log.xml'.format(step_id))
        scamp = api.Astromatic(**api_kwargs)
        result = scamp.run(catalogs)
        return result
    
    def run_swarp(self, step_id, filenames, api_kwargs, frames=None):
        """
        Run SWARP with a specified set of parameters
        
        Parameters
        ----------
        step_id: str
            Unique identifier for the current step in the pipeline
        filenames: list
            List of filenames that are stacked together
        api_kwargs: dict
            Keyword arguments used to run SWARP
        frames: list (optional)
            Subset of frames to stack. Default value is ``None``, which stacks all of the
            image frames for each file
        
        Returns
        -------
        result: dict
            Result of the astromatic code execution. This will minimally contain a ``status``
            key, that indicates ``success`` or ``error``. Additional keys:
            - error_msg: str
                If there is an error and the user is storing the output or exporting XML metadata,
                ``error_msg`` will contain the error message generated by the code
            - output: str
                If ``store_output==True`` the output of the program execution is
                stored in the ``output`` value.
            - warnings: str
                If the WRITE_XML parameter is ``True`` then a table of warnings detected
                in the code is returned
        """
        if 'code' not in api_kwargs:
            api_kwargs['code'] = 'SWarp'
        if 'cmd' not in api_kwargs and 'SWARP' in self.build_paths:
            api_kwargs['cmd'] = self.build_paths['SWARP']
        if 'temp_path' not in api_kwargs:
            api_kwargs['temp_path'] = self.temp_path
        if 'config' not in api_kwargs:
            api_kwargs['config'] = {}
        if 'RESAMPLE_DIR' not in api_kwargs['config']:
            api_kwargs['config']['RESAMPLE_DIR'] = api_kwargs['temp_path']
        if 'IMAGEOUT_NAME' not in api_kwargs['config']:
            raise PipelineError('Must include a name for the new stacked image')
        if 'WRITE_XML' not in api_kwargs['config']:
            api_kwargs['config']['WRITE_XML'] = 'Y'
        if 'XML_NAME' not in api_kwargs['config']:
            api_kwargs['config']['XML_NAME'] = os.path.join(pipeline.log_path, 
                '{0}.scamp.log.xml'.format(step_id))
        swarp = api.Astromatic(**api_kwargs)
        if frames is None:
            result = swarp.run(filenames)
        else:
            result = swarp.run_frames(files['image'], 'SWarp', frames, False)
        return result
    
    def run_psfex(self, step_id, catalogs, api_kwargs={}):
        """
        Run PSFEx with a specified set of parameters.
        
        Parameters
        ----------
        step_id: str
            Unique identifier for the current step in the pipeline
        catalogs: str or list
            catalog filename (or list of catalog filenames) to use
        api_kwargs: dict
            Keyword arguements to pass to PSFEx
        
        Returns
        -------
        result: dict
            Result of the astromatic code execution. This will minimally contain a ``status``
            key, that indicates ``success`` or ``error``. Additional keys:
            - error_msg: str
                If there is an error and the user is storing the output or exporting XML metadata,
                ``error_msg`` will contain the error message generated by the code
            - output: str
                If ``store_output==True`` the output of the program execution is
                stored in the ``output`` value.
            - warnings: str
                If the WRITE_XML parameter is ``True`` then a table of warnings detected
                in the code is returned
        """
        if 'code' not in api_kwargs:
            api_kwargs['code'] = 'PSFEx'
        if 'cmd' not in api_kwargs and 'PSFEx' in self.build_paths:
            api_kwargs['cmd'] = self.build_paths['PSFEx']
        if 'temp_path' not in api_kwargs:
            api_kwargs['temp_path'] = self.temp_path
        if 'config' not in api_kwargs:
            api_kwargs['config'] = {}
        if 'WRITE_XML' not in api_kwargs['config']:
            api_kwargs['config']['WRITE_XML'] = 'Y'
        if 'XML_NAME' not in api_kwargs['config']:
            api_kwargs['config']['XML_NAME'] = os.path.join(pipeline.log_path, 
                '{0}.psfex.log.xml'.format(step_id))
        psfex = api.Astromatic(**api_kwargs)
        result = psfex.run(catalogs)
        return result
    
    def run_swarp_old(self, step_id, filenames, stack_filename=None, api_kwargs={}, 
            frames=None, run_type='both'):
        """
        Run SWARP with a specified set of parameters
        
        Parameters
        ----------
        step_id: str
            Unique identifier for the current step in the pipeline
        filenames: list
            List of filenames that are stacked together
        stack_filename: str (optional)
            Name of final stacked image. If the user is only resampling but not stacking
            (``run_type='resample'``), this variable is ignored.
        api_kwargs: dict
            Keyword arguments used to run SWARP
        frames: list (optional)
            Subset of frames to stack. Default value is ``None``, which stacks all of the
            image frames for each file
        run_type: str
            How SCAMP will be run. Can be ``resample`` or ``stack`` or ``both``, which
            resamples and stacks the images.
        """
        logger.info('filenames:', filenames)
        if 'code' not in api_kwargs:
            api_kwargs['code'] = 'SWarp'
        if 'cmd' not in api_kwargs and 'SWARP' in self.build_paths:
            api_kwargs['cmd'] = self.build_paths['SWARP']
        if 'temp_path' not in api_kwargs:
            api_kwargs['temp_path'] = self.temp_path
        if 'config' not in api_kwargs:
            api_kwargs['config'] = {}
        if 'RESAMPLE_DIR' not in api_kwargs['config']:
            api_kwargs['config']['RESAMPLE_DIR'] = api_kwargs['temp_path']
        if 'XML_NAME' in api_kwargs['config']:
            xml_name = api_kwargs['config']['XML_NAME']
        else:
            xml_name = None
        if run_type=='both' or run_type=='resample':
            # Resample images as specified by WCS keywords in their headers
            logger.info("Create resampled images")
            kwargs = copy.deepcopy(api_kwargs)
            kwargs['config']['COMBINE'] = 'N'
            if xml_name is not None:
                kwargs['config']['XML_NAME'] = xml_name.replace('.xml', '-resamp.xml')
            swarp = api.Astromatic(**kwargs)
            result = swarp.run(filenames)
            if result['status']!='success':
                raise PipelineError("Error running SWARP")
        if run_type=='both' or run_type=='stack':
            logger.info('Creating stack for each CCD')
            if stack_filename is None:
                raise PipelineError("Must include a stack_filename to stack a set of images")
            kwargs = copy.deepcopy(api_kwargs)
            kwargs['config']['RESAMPLE'] = 'N'
            if frames is None:
                hdulist = fits.open(filenames[0])
                frames = range(1,len(hdulist))
                hdulist.close()
            # Temporarily create a stack for each frame
            for frame in frames:
                resamp_names = [f.replace('.fits', '.{0:04d}.resamp.fits'.format(frame)) 
                    for f in filenames]
                stack_frame = os.path.join(kwargs['temp_path'], 
                    os.path.basename(stack_filename).replace('.fits', 
                    '-{0:04d}.stack.fits'.format(frame)))
                kwargs['config']['IMAGEOUT_NAME'] = stack_frame
                kwargs['config']['WEIGHTOUT_NAME'] = stack_frame.replace('.fits', '.weight.fits')
                kwargs['config']['WEIGHT_SUFFIX'] = '.weight.fits'
                if xml_name is not None:
                    kwargs['config']['XML_NAME'] = xml_name.replace(
                        '.xml', '-stack-{0}.xml'.format(frame))
                swarp = api.Astromatic(**kwargs)
                result = swarp.run(resamp_names)
                if result['status']!='success':
                    raise PipelineError("Error running SWARP")
            
            # Combine the frame stacks into a single stacked image
            logger.info("Combining into single stack")
            primary = fits.PrimaryHDU()
            stack = [primary]
            weights = [primary]
            for frame in frames:
                stack_frame = os.path.join(kwargs['temp_path'], 
                    os.path.basename(stack_filename).replace('.fits', 
                    '-{0:04d}.stack.fits'.format(frame)))
                weight_frame = stack_frame.replace('.fits', '.weight.fits')
                hdulist = fits.open(stack_frame)
                stack.append(fits.ImageHDU(hdulist[0].data,hdulist[0].header))
                hdulist.close()
                hdulist = fits.open(weight_frame)
                weights.append(fits.ImageHDU(hdulist[0].data,hdulist[0].header))
            weight_name = stack_filename.replace('.fits', '.wtmap.fits')
            stack = fits.HDUList(stack)
            stack.writeto(stack_filename, clobber=True)
            stack.close()
            weights = fits.HDUList(weights)
            weights.writeto(weight_name, clobber=True)
            weights.close()
     
    def add_step(self, func, tags, **kwargs):
        """
        Add a new `PipelineStep` to the pipeline
        
        Parameters
        ----------
        func: function or string
            If ``func`` is a string this should be a 
        """
        if isinstance(func, string_types):
            if func in api.codes:
                if func == 'SExtractor':
                    func = self.run_sex
                elif func == 'SCAMP':
                    func = self.run_scamp
                elif func == 'PSFEx':
                    func = self.run_psfex
                elif func == 'SWARP':
                    func = self.run_swarp
                else:
                    raise PipelineError("You must either pass a function for the pipeline "
                        "to run or the name of an astromatic code")
            else:
                raise PipelineError("You must either pass a function for the pipeline "
                    "to run or the name of an astromatic code")
        step_id = self.next_id
        self.next_id += 1
        self.steps.append(PipelineStep(
            func,
            step_id,
            tags,
            kwargs
        ))
            
    def run(self, run_tags=[], ignore_tags=[], pipeline_steps=None):
        """
        Run the pipeline given a list of PipelineSteps
        
        Parameters
        ----------
        run_tags: list
            Run all steps that have a tag listed in ``run_tags`` and not in ``ignore_tags``.
            If ``len(run_tags)==0`` then all of the steps are run that are not listed 
            in ignore tags.
        ignore_tags: list
            Ignore all steps that contain one of the tags in ``ignore_tags``.
        pipeline_steps: list of `PipelineStep` (optional)
            Instead of running the steps associated with a pipeline, the user can specify
            a set of steps to run. This can be useful if (for example) mulitple criteria
            are used to select steps to run and the user wants to perform these cuts in
            some other function to generate the necessary steps to run.
        logfile: filename or file object
            Keeps track of which steps have been run. Each time a step is run it is
            logged in the log file so that if there is an error that causes the pipeline
            to stop, the user can pick up where he/she left off.
        """
        if pipeline_steps is None:
            pipeline_steps = self.steps
        
        steps = [step for step in pipeline steps if
            (len(run_tags) == 0 or any([tag in run_tags for tag in self.tags])) and
            not any([tag in ignore_tags for tag in self.tags])]
        
        all_warnings = None
        for step in steps:
            result = step.func(step.ste_id, **step.func_kwargs)
            if 'warnings' in result:
                from astropy.table import vstack
                warnings = result['warnings']
                warnings['filename'] = result.meta['filename']
                warnings['step'] = step.step_id
                if all_warnings is None:
                    all_warnings = warnings
                else:
                    all_warnings = vstack([all_warnings, warnings])
            if result['status'] == 'error':
                result = {
                    'status': 'error',
                    'function_result': result,
                    'warnings': all_warnings
                    'log': log
                }
                return result
        
        result = {
            'status': 'success',
            'warnings': all_warnings
        }
        return result

class PipelineStep:
    """
    A single step in the pipeline. This takes a function and a set of tags and kwargs
    associated with it and stores them in the pipeline.
    """
    def __init__(self, func, step_id, tags=[], func_kwargs):
        """
        Initialize a PipelineStep object
        
        Parameters
        ----------
        func: function
            The function to be run
        id: str
            Unique identifier for the step
        tags: list
            A list of tags used to identify the step. When running the pipeline the user
            can specify a set of conditions that will filter which steps are run (or not run)
            based on a set of specified tags
        func_kwargs: dict
            Keyword arguments passed to the ``func`` when the pipeline is run
        """
        self.func = func
        self.tags = tags
        self.step_id = step_id
        self.func_kwargs = func_kwargs