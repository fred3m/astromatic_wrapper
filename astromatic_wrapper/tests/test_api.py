import sys
if sys.version_info > (3,0):
    import builtins
else:
    import __builtin__ as builtins
import os
import subprocess
from astropy.extern import six
import copy
from astropy.tests.helper import pytest
from collections import OrderedDict

from astromatic_wrapper import api
from astromatic_wrapper.utils import ldac, pipeline

def setup_module(module):
    module.data_path = os.path.join(os.path.relpath(__file__), 'data')

def mock_subprocess_call(return_val):
    # Mock the subprocess so that it doesn't actually execute subprocess.call,
    # which might require third party software installed on the system
    def f(cmd, shell=False, **kwargs):
        if not isinstance(cmd, six.string_types):
            cmd = ' '.join(cmd)
        return return_val
    return f

def mock_raw_input(return_val):
    def f(*args, **kwargs):
        return return_val
    return f

def mock_run_cmd(*args, **kwargs):
    return {'status': 'error', 'args': args[1:], 'kwargs':kwargs}

class TestAstromatic:
    def test_init(self, tmpdir):
        sex_kwargs = {
            'code': 'SExtractor',
            'temp_path': str(tmpdir),
            'config': {
                'CATALOG_NAME': 'test.fits',
                'CATALOG_TYPE': 'FITS_LDAC',
                'PARAMETERS_NAME': 'default.path',
            },
            'config_file': 'path/to/config/file',
        }
        kwargs = copy.deepcopy(sex_kwargs)
        kwargs['params'] = ['X_WORLD']
        sextractor = api.Astromatic(**kwargs)
        assert sextractor.code == 'SExtractor'
        assert sextractor.temp_path == sex_kwargs['temp_path']
        assert sextractor.config['PARAMETERS_NAME'] == sex_kwargs['config']['PARAMETERS_NAME']
        assert sextractor.config_file == sex_kwargs['config_file']
        assert sextractor.params == ['X_WORLD']
    
    def test_build_cmd(self,tmpdir):
        sex_kwargs = {
            'code': 'SExtractor',
            'temp_path': str(tmpdir),
            'config': OrderedDict([
                ('CATALOG_NAME', 'test.fits'),
                ('CATALOG_TYPE', 'FITS_LDAC'),
                ('PARAMETERS_NAME', 'default.path'),
                ('FILTER', False),
            ]),
            'config_file': 'path/to/config/file',
        }
        build_paths = {'SExtractor': 'path/to/sex'}
        kwargs = copy.deepcopy(sex_kwargs)
        sextractor = api.Astromatic(**kwargs)
        cmd_result = 'sex test.fits -c {0} -CATALOG_NAME {1} '.format(
            sex_kwargs['config_file'], sex_kwargs['config']['CATALOG_NAME'])
        cmd_result += '-CATALOG_TYPE FITS_LDAC -PARAMETERS_NAME default.path -FILTER N'
        assert sextractor.build_cmd('test.fits')[0]==cmd_result
        
        kwargs = copy.deepcopy(sex_kwargs)
        sextractor = api.Astromatic('SExtractor')
        kwargs['cmd'] = 'path/to/sex'
        del kwargs['config_file']
        kwargs['params'] = ['X_WORLD', 'Y_WORLD', 'MAG_AUTO']
        cmd_result = 'path/to/sex test.fits -CATALOG_NAME {0} '.format(
            sex_kwargs['config']['CATALOG_NAME'])
        cmd_result += '-CATALOG_TYPE FITS_LDAC -PARAMETERS_NAME {0} -FILTER N'.format(
            os.path.join(str(tmpdir), 'sex.param'))
        assert sextractor.build_cmd('test.fits', **kwargs)[0]==cmd_result
    
    def test_run_frames(self, tmpdir):
        import subprocess
        import types
        
        sex_kwargs = {
            'code': 'SExtractor',
            'temp_path': str(tmpdir),
            'config': OrderedDict([
                ('CATALOG_NAME', 'test.fits'),
                ('PARAMETERS_NAME', 'default.path'),
                ('WEIGHT_IMAGE', 'test.wtmap.fits'),
                ('FLAG_IMAGE', 'test.dqmask.fits')
            ]),
        }
        subprocess.call = mock_subprocess_call(0)
        sextractor = api.Astromatic(**sex_kwargs)
        sextractor._run_cmd = types.MethodType(mock_run_cmd, sextractor)
        frame_result = sextractor.run_frames('test.fits', frames=[2])
        result = {
            #'args': ('sex test.fits[2] -PARAMETERS_NAME default.path -WEIGHT_IMAGE'
            #        ' test.wtmap.fits[2] -CATALOG_NAME test.fits[2] '
            #        '-FLAG_IMAGE test.dqmask.fits[2]',
            'args': (
                'sex test.fits[2] -CATALOG_NAME test.fits[2] -PARAMETERS_NAME default.path '
                    '-WEIGHT_IMAGE test.wtmap.fits[2] -FLAG_IMAGE test.dqmask.fits[2]',
                False,
                None,
                True),
            'kwargs': {'frame': '2'},
            'status': 'error',
            'warnings': None
        }
        assert frame_result==result
    
    def test_version(self):
        import subprocess
        def mock_subprocess_popen(*args, **kwargs):
            class stdout:
                def readlines(self):
                    return ['SExtractor version 2.19.5 (2015-04-30)\n']
            class popen:
                def __init__(self):
                    self.stdout = stdout()
            return popen()
        subprocess.Popen = mock_subprocess_popen
        sextractor = api.Astromatic('SExtractor')
        assert sextractor.get_version()==('2.19.5', '2015-04-30')

api.Astromatic._run_cmd = mock_run_cmd

def test_run_sex(tmpdir):
    paths = {
        'temp': os.path.join(str(tmpdir), 'temp'),
        'log': os.path.join(str(tmpdir), 'log')
    }
    setattr(builtins,'raw_input', mock_raw_input('y'))
    setattr(builtins,'input', mock_raw_input('y'))
    pipe = pipeline.Pipeline(paths=paths, build_paths = {})
    files = {
        'image': 'img.fits',
        'dqmask': 'img.dqmask.fits',
        'wtmap': 'img.wtmap.fits'
    }
    kwargs = {
        'config': OrderedDict([
            ('PARAMETERS_NAME', 'default.path'),
        ])
    }
    result = api.run_sex(pipe,0,files, kwargs)
    cmd = 'sex img.fits -PARAMETERS_NAME default.path -CATALOG_NAME img.cat '
    cmd += '-FLAG_IMAGE img.dqmask.fits -WEIGHT_IMAGE img.wtmap.fits '
    cmd += '-WRITE_XML Y -XML_NAME {0}/0.sex.log.xml'.format(paths['log'])
    cmd_result = {
        'args': (
            cmd,
            False,
            '{0}/0.sex.log.xml'.format(paths['log']),
            True),
        'kwargs': {},
        'status': 'error'
    }
    assert result==cmd_result
    
    result = api.run_sex(pipe,0,files, kwargs, [1])
    cmd = 'sex img.fits[1] -PARAMETERS_NAME default.path -CATALOG_NAME img.cat '
    cmd += '-FLAG_IMAGE img.dqmask.fits[1] -WEIGHT_IMAGE img.wtmap.fits[1] '
    cmd += '-WRITE_XML Y -XML_NAME {0}/0.sex.log-1.xml'.format(paths['log'])
    cmd_result = {
        'args': (
            cmd,
            False,
            '{0}/0.sex.log.xml'.format(paths['log']),
            False),
        'kwargs': {'frame': '1'},
        'status': 'error',
        'warnings': None
    }
    assert result == cmd_result

def test_run_scamp(tmpdir):
    paths = {
        'temp': os.path.join(str(tmpdir), 'temp'),
        'log': os.path.join(str(tmpdir), 'log')
    }
    setattr(builtins,'raw_input', mock_raw_input('y'))
    setattr(builtins,'input', mock_raw_input('y'))
    pipe = pipeline.Pipeline(paths=paths, build_paths = {})
    result = api.run_scamp(pipe,0,['cat1.fits','cat2.fits'], {}, 'new_cat.fits')
    cmd = 'scamp cat1.fits cat2.fits -SAVE_REFCATALOG Y -REFOUT_CATPATH new_cat.fits '
    cmd += '-WRITE_XML Y -XML_NAME {0}/0.scamp.log.xml'.format(paths['log'])
    cmd_result = {
        'args': (
            cmd,
            False,
            '{0}/0.scamp.log.xml'.format(paths['log']),
            True),
        'kwargs': {},
        'status': 'error'
    }
    assert result==cmd_result

def test_run_swarp(tmpdir):
    paths = {
        'temp': os.path.join(str(tmpdir), 'temp'),
        'log': os.path.join(str(tmpdir), 'log')
    }
    setattr(builtins,'raw_input', mock_raw_input('y'))
    setattr(builtins,'input', mock_raw_input('y'))
    pipe = pipeline.Pipeline(paths=paths, build_paths = {})
    result = api.run_swarp(pipe,0,['img1.fits','img2.fits'], {})
    cmd = 'swarp img1.fits img2.fits -RESAMPLE_DIR {0} '.format(paths['temp'])
    cmd += '-WRITE_XML Y -XML_NAME {0}/0.swarp.log.xml'.format(paths['log'])
    cmd_result = {
        'args': (
            cmd,
            False,
            '{0}/0.swarp.log.xml'.format(paths['log']),
            True),
        'kwargs': {},
        'status': 'error'
    }
    assert result==cmd_result
    
    result = api.run_swarp(pipe,0,['img1.fits','img2.fits'], {}, frames=[1])
    cmd = 'swarp img1.fits[1] img2.fits[1] -RESAMPLE_DIR {0} '.format(paths['temp'])
    cmd += '-WRITE_XML Y -XML_NAME {0}/0.swarp.log-1.xml'.format(paths['log'])
    cmd_result = {
        'args': (
            cmd,
            False,
            '{0}/0.swarp.log.xml'.format(paths['log']),
            False),
        'kwargs': {'frame': '1'},
        'status': 'error',
        'warnings': None
    }
    assert result==cmd_result

def test_run_psfex(tmpdir):
    paths = {
        'temp': os.path.join(str(tmpdir), 'temp'),
        'log': os.path.join(str(tmpdir), 'log')
    }
    setattr(builtins,'raw_input', mock_raw_input('y'))
    setattr(builtins,'input', mock_raw_input('y'))
    pipe = pipeline.Pipeline(paths=paths, build_paths = {})
    result = api.run_psfex(pipe,0,['cat1.fits','cat2.fits'], {})
    cmd = 'psfex cat1.fits cat2.fits -PSF_DIR {0} '.format(paths['temp'])
    cmd += '-WRITE_XML Y -XML_NAME {0}/0.psfex.log.xml'.format(paths['log'])
    cmd_result = {
        'args': (
            cmd,
            False,
            '{0}/0.psfex.log.xml'.format(paths['log']),
            True),
        'kwargs': {},
        'status': 'error'
    }
    assert result==cmd_result