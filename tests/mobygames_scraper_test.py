import unittest, os
import unittest.mock
from unittest.mock import MagicMock, patch

import json
import re
import logging

from fakes import FakeProgressDialog, random_string

logging.basicConfig(format = '%(asctime)s %(module)s %(levelname)s: %(message)s',
                datefmt = '%m/%d/%Y %I:%M:%S %p', level = logging.DEBUG)
logger = logging.getLogger(__name__)

from resources.lib.scraper import MobyGames
from ael.scrapers import ScrapeStrategy, ScraperSettings

from ael.api import ROMObj
from ael import constants
from ael.utils import net
        
def read_file(path):
    with open(path, 'r') as f:
        return f.read()
    
def read_file_as_json(path):
    file_data = read_file(path)
    return json.loads(file_data, encoding = 'utf-8')

def mocked_mobygames(url, url_log=None):

    mocked_json_file = ''

    if 'format=brief&title=' in url:
        mocked_json_file = Test_mobygames_scraper.TEST_ASSETS_DIR + "\\mobygames_castlevania_list.json"

    if 'screenshots' in url:
        mocked_json_file = Test_mobygames_scraper.TEST_ASSETS_DIR + "\\mobygames_castlevania_screenshots.json"

    if 'covers' in url:
        mocked_json_file = Test_mobygames_scraper.TEST_ASSETS_DIR + "\\mobygames_castlevania_covers.json"
                        
    if re.search('/games/(\d*)\?', url):
        mocked_json_file = Test_mobygames_scraper.TEST_ASSETS_DIR + "\\mobygames_castlevania.json"
        
    if mocked_json_file == '':
        return net.get_URL(url)

    print('reading mocked data from file: {}'.format(mocked_json_file))
    return read_file(mocked_json_file), 200

class Test_mobygames_scraper(unittest.TestCase):
    
    ROOT_DIR = ''
    TEST_DIR = ''
    TEST_ASSETS_DIR = ''

    @classmethod
    def setUpClass(cls):        
        cls.TEST_DIR = os.path.dirname(os.path.abspath(__file__))
        cls.ROOT_DIR = os.path.abspath(os.path.join(cls.TEST_DIR, os.pardir))
        cls.TEST_ASSETS_DIR = os.path.abspath(os.path.join(cls.TEST_DIR,'assets/'))
                
        print('ROOT DIR: {}'.format(cls.ROOT_DIR))
        print('TEST DIR: {}'.format(cls.TEST_DIR))
        print('TEST ASSETS DIR: {}'.format(cls.TEST_ASSETS_DIR))
        print('---------------------------------------------------------------------------')

    @patch('resources.lib.scraper.net.get_URL', side_effect = mocked_mobygames)
    @patch('resources.lib.scraper.settings.getSetting', autospec=True)
    @patch('ael.api.client_get_rom')
    def test_scraping_metadata_for_game(self, api_rom_mock: MagicMock, settings_mock:MagicMock, mock_get):    
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
            'scanned_data': { 'file':Test_mobygames_scraper.TEST_ASSETS_DIR + '\\castlevania.zip'},
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
    @patch('resources.lib.scraper.net.get_URL', side_effect = mocked_mobygames)
    @patch('resources.lib.scraper.net.download_img')
    @patch('resources.lib.scraper.io.FileName.scanFilesInPath', autospec=True)
    @patch('resources.lib.scraper.settings.getSetting', autospec=True)
    @patch('ael.api.client_get_rom')
    def test_scraping_assets_for_game(self, api_rom_mock: MagicMock, settings_mock:MagicMock, scan_mock, mock_imgs, mock_get):
        # arrange
        settings_mock.side_effect = lambda key: random_string(12) if key == 'scraper_mobygames_apikey' else ''
        
        settings = ScraperSettings()
        settings.scrape_metadata_policy = constants.SCRAPE_ACTION_NONE
        settings.scrape_assets_policy = constants.SCRAPE_POLICY_SCRAPE_ONLY
        settings.asset_IDs_to_scrape = [constants.ASSET_BOXFRONT_ID, constants.ASSET_BOXBACK_ID, constants.ASSET_SNAP_ID ]
        
        rom_id = random_string(5)
        rom = ROMObj({
            'id': rom_id,
            'scanned_data': { 'file': Test_mobygames_scraper.TEST_ASSETS_DIR + '\\castlevania.zip'},
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