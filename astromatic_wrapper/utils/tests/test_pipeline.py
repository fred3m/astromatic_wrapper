from __future__ import division
import sys
if sys.version_info > (3,0):
    import builtins
else:
    import __builtin__ as builtins
import os
from astropy.io import fits
from astropy.table import Table
from astropy.tests.helper import pytest
import dill

from astromatic_wrapper.utils import pipeline

def mock_raw_input(return_val):
    def f(*args, **kwargs):
        return return_val
    return f

@pytest.mark.parametrize(('bool_str', 'bool_val'),
    [('YeS', True), ('TrUe',True), ('nO',False),('fALse', False)])
def test_str_2_bool(bool_str, bool_val):
    assert pipeline.str_2_bool(bool_str)==bool_val

def test_check_path(tmpdir):
    setattr(builtins,'raw_input', mock_raw_input('y'))
    setattr(builtins,'input', mock_raw_input('y'))
    pipeline.check_path(os.path.join(str(tmpdir), 'path1'))
    setattr(builtins,'raw_input', mock_raw_input('n'))
    setattr(builtins,'input', mock_raw_input('n'))
    with pytest.raises(pipeline.PipelineError):
        pipeline.check_path(os.path.join(str(tmpdir), 'path2'))

@pytest.fixture
def test_func1(pipeline, step_id, var1, var2):
    result = {
        'status': 'success',
        'next_id': pipeline.next_id,
        'step_id': step_id,
        'sum': var1+var2
    }
    return result
@pytest.fixture    
def test_func2(var1, var2):
    if var2==0:
        result = {
            'status': 'error',
            'error': 'Division by 0'
        }
    else:
        result = {
            'status': 'success',
            'diff': var1/var2
        }
    return result
@pytest.fixture
def test_func3(var1,var2):
    return {
        'status': 'success',
        'diff': var1/var2
    }

class TestPipeline:
    def test_empty_init(self):
        pipe = pipeline.Pipeline()
        assert pipe.create_paths==False
        assert pipe.steps==[]
        assert pipe.next_id==0
        assert pipe.run_steps==None
        assert pipe.run_warnings==None
        assert pipe.run_step_idx==0
        assert pipe.paths=={}
    
    def test_init(self, tmpdir):
        temp_path = os.path.join(str(tmpdir), 'temp')
        log_path = os.path.join(str(tmpdir), 'log')
        os.makedirs(log_path)
        kwargs = {
            'paths': {
                'temp': temp_path,
                'log': log_path
            },
            'steps': [1,2,3,4],
            'next_id': 5,
            'run_steps': [2,4],
            'run_warnings': 'dummy value',
            'run_step_idx': 1,
            'dummy_key': 'added me too!'
        }
        with pytest.raises(pipeline.PipelineError):
            pipe = pipeline.Pipeline(**kwargs)
        
        pipe = pipeline.Pipeline(create_paths=True, pipeline_name='test_pipeline', **kwargs)
        for k,v in kwargs.items():
            assert getattr(pipe,k) == v
        assert pipe.name == 'test_pipeline'
    
    def test_add_step(self):
        def test_function(pipeline, step_id, var1, var2):
            result = {
                'status': success,
                'next_id': pipeline.next_id,
                'step_id': step_id,
                'sum': var1+var2
            }
            return result
        
        pipe = pipeline.Pipeline()
        pipe.add_step(test_function, ['tag1','tag2'], var1=5, var2=10)
        step = pipe.steps[0]
        assert len(pipe.steps)==1
        assert pipe.next_id==1
        assert step.func==test_function
        assert set(step.tags)==set(['tag1','tag2'])
        assert step.func_kwargs=={'var1':5,'var2':10}
        assert step.results==None
    
    def test_run_basic(self, tmpdir):
        temp_path = os.path.join(str(tmpdir), 'temp')
        log_path = os.path.join(str(tmpdir), 'log')
        paths = {
            'temp': temp_path,
            'log': log_path
        }
        pipe = pipeline.Pipeline(paths=paths, create_paths=True)

        pipe.add_step(test_func1, ['func1'], var1=3, var2=4)
        pipe.add_step(test_func2, ['func2'], var1=25, var2=10)
        pipe.add_step(test_func2, ['func2'], var1=1, var2=0)
        pipe.add_step(test_func3, var1=1, var2=0)
        result = pipe.run(ignore_errors=True, ignore_exceptions=True)
        assert result['status']=='success'
        assert pipe.steps[0].results=={'next_id': 4, 'status': 'success', 'step_id': 0, 'sum': 7}
        assert pipe.steps[1].results=={'diff': 2.5, 'status': 'success'}
        assert pipe.steps[2].results=={'error': 'Division by 0', 'status': 'error'}
        assert pipe.steps[3].results['status']=='error'
        
        for step in pipe.steps:
            step.results = None
        result = pipe.run(['func2'], ignore_errors=True, ignore_exceptions=True)
        assert pipe.steps[0].results==None
        assert pipe.steps[1].results=={'diff': 2.5, 'status': 'success'}
        assert pipe.steps[2].results=={'error': 'Division by 0', 'status': 'error'}
        assert pipe.steps[3].results==None
        
        for step in pipe.steps:
            step.results = None
        result = pipe.run(ignore_tags=['func2'], ignore_errors=True, ignore_exceptions=True)
        assert pipe.steps[0].results=={'next_id': 4, 'status': 'success', 'step_id': 0, 'sum': 7}
        assert pipe.steps[1].results==None
        assert pipe.steps[2].results==None
        assert pipe.steps[3].results['status']=='error'
    
    def test_run_advanced(self, tmpdir):
        temp_path = os.path.join(str(tmpdir), 'temp')
        log_path = os.path.join(str(tmpdir), 'log')
        paths = {
            'temp': temp_path,
            'log': log_path
        }
        pipe = pipeline.Pipeline(paths=paths, create_paths=True)
        pipe.add_step(test_func1, ['func1'], var1=3, var2=4)
        pipe.add_step(test_func2, ['func2'], var1=25, var2=10)
        pipe.add_step(test_func2, ['func2'], var1=1, var2=0)
        pipe.add_step(test_func3, var1=1, var2=0)
        
        with pytest.raises(pipeline.PipelineError):
            pipe.run()
        pipe = dill.load(open(os.path.join(paths['log'], 'pipeline.p'), 'rb'))
        assert pipe.run_step_idx==2
        assert pipe.steps[0].results=={'next_id': 4, 'status': 'success', 'step_id': 0, 'sum': 7}
        
        with pytest.raises(ZeroDivisionError):
            for step in pipe.steps:
                step.results = None
            pipe.run(resume=True, ignore_errors=True)
        
        new_pipe = dill.load(open(os.path.join(paths['log'], 'pipeline.p'), 'rb'))
        result = new_pipe.run(start_idx=1, ignore_errors=True, ignore_exceptions=True)
        assert result['status']=='success'
        assert new_pipe.steps[0].results==None
        assert new_pipe.steps[1].results=={'diff': 2.5, 'status': 'success'}
        assert new_pipe.steps[2].results=={'error': 'Division by 0', 'status': 'error'}
        assert new_pipe.steps[3].results['status']=='error'