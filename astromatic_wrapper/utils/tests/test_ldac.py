import os
from astropy.io import fits
from astropy.table import Table
from astropy.tests.helper import pytest

from astromatic_wrapper.utils import ldac

def setup_module(module):
    import numpy as np
    module.tbl_data =[
        np.array([(220.59332925263806, 0.7538374873328122, -9.60145092010498),
            (220.5778728622028, 0.7502730046087462, -12.5360689163208),
            (220.61444985607636, 0.750653514185006, -9.78681755065918),
            (220.61804230607706, 0.7497301153836181, -6.500776767730713),
            (220.43532765178765, 0.8969403740644865, -13.243828773498535),
            (220.49598500579978, 0.8967630969635536, -7.345831871032715),
            (220.5077939858399, 0.8968532263340241, -8.0485200881958),
            (220.62280988628237, 0.8962803356404196, -7.721217155456543),
            (220.4305447443208, 0.8960707108954606, -10.320489883422852),
            (220.41366141203562, 0.8958679788408644, -7.686360836029053)], 
            dtype=[('XWIN_WORLD', '>f8'), ('YWIN_WORLD', '>f8'), ('MAG_AUTO', '>f4')]),
        np.array([(220.50064966960093, 0.8955663781120097, -8.910843849182129),
            (220.4968801048523, 0.8954698962325842, -8.470935821533203),
            (220.59708436324044, 0.8952249600123433, -8.644355773925781),
            (220.587911968118, 0.8949625378106356, -7.812751770019531),
            (220.589755212534, 0.8944211816957558, -7.691015243530273),
            (220.42120144220732, 0.8942797762215124, -6.929902076721191),
            (220.5693232344265, 0.8932321555198349, -7.903119087219238),
            (220.5566775733446, 0.8927124746776108, -6.447216033935547),
            (220.38187525710657, 0.8923323696788624, -7.403841972351074),
            (220.629789321442, 0.8925150653438292, -6.726459503173828)], 
            dtype=[('XWIN_WORLD', '>f8'), ('YWIN_WORLD', '>f8'), ('MAG_AUTO', '>f4')])
    ]

data_path = os.path.join(os.path.dirname(os.path.relpath(__file__)), 'data')

@pytest.mark.parametrize(('filename', 'frame'),
    [(os.path.join(data_path, 'test.ldac.fits'),1),
        (os.path.join(data_path, 'multiext.ldac.fits'), 2)])
def test_get_table_from_ldac(filename, frame):
    data_tbl = Table(tbl_data[frame-1])
    test_tbl = ldac.get_table_from_ldac(filename, frame)
    assert all(data_tbl==test_tbl)

def test_convert_table_to_ldac():
    tbl = Table(tbl_data[0])
    hdulist = fits.open(os.path.join(data_path, 'test.ldac.fits'))
    new_hdulist = ldac.convert_table_to_ldac(tbl)
    for m in range(len(hdulist)):
        for n in range(len(hdulist[m].header.cards)):
            assert set(new_hdulist[m].header.cards[n])==set(hdulist[m].header.cards[n])

def test_save_table_as_ldac(tmpdir):
    tbl = Table(tbl_data[0])
    hdulist = fits.open(os.path.join(data_path, 'test.ldac.fits'))
    filename = os.path.join(str(tmpdir), 'temp.ldac.fits')
    ldac.save_table_as_ldac(tbl, filename)
    new_hdulist = fits.open(filename)
    for m in range(len(hdulist)):
        for n in range(len(hdulist[m].header.cards)):
            assert set(new_hdulist[m].header.cards[n])==set(hdulist[m].header.cards[n])