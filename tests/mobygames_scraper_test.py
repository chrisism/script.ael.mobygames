import unittest, os
import unittest.mock
from unittest.mock import MagicMock, patch

import json
import re
import logging

from tests.fakes import FakeProgressDialog, FakeFile, random_string

#logging.basicConfig(format = '%(asctime)s %(module)s %(levelname)s: %(message)s',
#                datefmt = '%m/%d/%Y %I:%M:%S %p', level = logging.DEBUG)
logger = logging.getLogger(__name__)

from resources.lib.scraper import MobyGames
from akl.scrapers import ScrapeStrategy, ScraperSettings

from akl.api import ROMObj
from akl import constants
from akl.utils import net
        
def read_file(path):
    with open(path, 'r') as f:
        return f.read()
    
def read_file_as_json(path):
    file_data = read_file(path)
    return json.loads(file_data, encoding = 'utf-8')

def mocked_mobygames(url, url_log=None):
    TEST_DIR = os.path.dirname(os.path.abspath(__file__))
    TEST_ASSETS_DIR = os.path.abspath(os.path.join(TEST_DIR,'assets/'))

    if 'format=brief&title=' in url:
        mocked_json_file = TEST_ASSETS_DIR + "/mobygames_castlevania_list.json"
        return read_file(mocked_json_file), 200

    if 'screenshots' in url:
        mocked_json_file = TEST_ASSETS_DIR + "/mobygames_castlevania_screenshots.json"
        return read_file(mocked_json_file), 200

    if 'covers' in url:
        mocked_json_file = TEST_ASSETS_DIR + "/mobygames_castlevania_covers.json"
        return read_file(mocked_json_file), 200
                        
    if re.search(r'/games/(\d*)\/platforms', url):
        mocked_json_file = TEST_ASSETS_DIR + "/mobygames_castlevania_by_platform.json"
        return read_file(mocked_json_file), 200
        
    if re.search(r'/games/(\d*)\?', url):
        mocked_json_file = TEST_ASSETS_DIR + "/mobygames_castlevania.json"
        return read_file(mocked_json_file), 200
        
    return net.get_URL(url)

def get_setting(key:str):
    if key == 'scraper_cache_dir': return FakeFile('/cache')
    return ''

class Test_mobygames_scraper(unittest.TestCase):
    
    @patch('akl.scrapers.kodi.getAddonDir', autospec=True, return_value=FakeFile('/'))
    @patch('resources.lib.scraper.net.get_URL', side_effect = mocked_mobygames)
    @patch('resources.lib.scraper.settings.getSetting', autospec=True, side_effect=get_setting)
    @patch('akl.api.client_get_rom')
    def test_scraping_metadata_for_game(self, 
        api_rom_mock: MagicMock, settings_mock:MagicMock, mock_get, addon_dir):    
        """
        First test. Test metadata scraping.
        """
        print('BEGIN Test_mobygames_scraper::test_scraping_metadata_for_game()')    
        # arrange
        settings_mock.side_effect = lambda key: random_string(12) if key == 'scraper_mobygames_apikey' else ''
        
        settings = ScraperSettings()
        settings.scrape_metadata_policy = constants.SCRAPE_POLICY_SCRAPE_ONLY
        settings.scrape_assets_policy = constants.SCRAPE_ACTION_NONE
        
        rom_id = random_string(5)
        rom = ROMObj({
            'id': rom_id,
            'scanned_data': { 'file':'fakedir/roms/castlevania.zip'},
            'platform': 'Nintendo NES'
        })
        api_rom_mock.return_value = rom
        
        target = ScrapeStrategy(None, 0, settings, MobyGames(), FakeProgressDialog())

        # act
        actual = target.process_single_rom(rom_id)
        
        # assert
        self.assertTrue(actual)
        self.assertEqual(u'Castlevania', actual.get_name())
        print(actual.get_data_dic())
                
    # add actual mobygames apikey above and comment out patch attributes to do live tests
    @patch('akl.scrapers.kodi.getAddonDir', autospec=True, return_value=FakeFile('/'))
    @patch('resources.lib.scraper.net.get_URL', side_effect = mocked_mobygames)
    @patch('resources.lib.scraper.net.download_img', autospec=True)
    @patch('resources.lib.scraper.io.FileName.scanFilesInPath', autospec=True)
    @patch('resources.lib.scraper.settings.getSetting', autospec=True, side_effect=get_setting)
    @patch('akl.api.client_get_rom')
    def test_scraping_assets_for_game(self, 
        api_rom_mock: MagicMock, settings_mock:MagicMock, scan_mock, 
        mock_imgs, mock_get, addon_dir):
        # arrange
        settings_mock.side_effect = lambda key: random_string(12) if key == 'scraper_mobygames_apikey' else ''
        
        settings = ScraperSettings()
        settings.scrape_metadata_policy = constants.SCRAPE_ACTION_NONE
        settings.scrape_assets_policy = constants.SCRAPE_POLICY_SCRAPE_ONLY
        settings.asset_IDs_to_scrape = [constants.ASSET_BOXFRONT_ID, constants.ASSET_BOXBACK_ID, constants.ASSET_SNAP_ID ]
        
        rom_id = random_string(5)
        rom = ROMObj({
            'id': rom_id,
            'scanned_data': { 'file': '/fakedir/roms/castlevania.zip'},
            'platform': 'Nintendo NES',
            'assets': {key: '' for key in constants.ROM_ASSET_ID_LIST},
            'asset_paths': {
                constants.ASSET_BOXFRONT_ID: '/fronts/',
                constants.ASSET_BOXBACK_ID: '/backs/',
                constants.ASSET_SNAP_ID: '/snaps/'
            }
        })
        api_rom_mock.return_value = rom
        
        target = ScrapeStrategy(None, 0, settings, MobyGames(), FakeProgressDialog())

        # act
        actual = target.process_single_rom(rom_id)

        # assert
        self.assertTrue(actual) 
        logger.info(actual.get_data_dic()) 
        
        self.assertTrue(actual.entity_data['assets'][constants.ASSET_BOXFRONT_ID], 'No boxfront defined')
        self.assertTrue(actual.entity_data['assets'][constants.ASSET_BOXBACK_ID], 'No boxback defined')
        self.assertTrue(actual.entity_data['assets'][constants.ASSET_SNAP_ID], 'No snap defined')      