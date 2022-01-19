#!/usr/bin/python -B
# -*- coding: utf-8 -*-
#
# Test AKL Mobybgames metadata scraper.
#

# --- Python standard library ---
from __future__ import unicode_literals
import os
import unittest
import unittest.mock
from unittest.mock import patch, MagicMock
import logging

logging.basicConfig(format = '%(asctime)s %(module)s %(levelname)s: %(message)s',
                datefmt = '%m/%d/%Y %I:%M:%S %p', level = logging.DEBUG)
logger = logging.getLogger(__name__)

from resources.lib.scraper import MobyGames
from akl.utils import kodi, io
from akl.api import ROMObj
from akl import constants

# --- Test data -----------------------------------------------------------------------------------
games = {
    # Console games
    'metroid'                : ('Metroid', 'Metroid.zip', 'Nintendo SNES'),
    'mworld'                 : ('Super Mario World', 'Super Mario World.zip', 'Nintendo SNES'),
    'sonic_megaDrive'        : ('Sonic the Hedgehog', 'Sonic the Hedgehog (USA, Europe).zip', 'Sega Mega Drive'),
    'sonic_genesis'          : ('Sonic the Hedgehog', 'Sonic the Hedgehog (USA, Europe).zip', 'Sega Genesis'),
    'chakan'                 : ('Chakan', 'Chakan (USA, Europe).zip', 'Sega MegaDrive'),
    'ff7'                    : ('Final Fantasy VII', 'Final Fantasy VII (USA) (Disc 1).iso', 'Sony PlayStation'),
    'console_wrong_title'    : ('Console invalid game', 'mjhyewqr.zip', 'Sega MegaDrive'),
    'console_wrong_platform' : ('Sonic the Hedgehog', 'Sonic the Hedgehog (USA, Europe).zip', 'mjhyewqr'),

    # MAME games
    'atetris'             : ('Tetris (set 1)', 'atetris.zip', 'MAME'),
    'mslug'               : ('Metal Slug - Super Vehicle-001', 'mslug.zip', 'MAME'),
    'dino'                : ('Cadillacs and Dinosaurs (World 930201)', 'dino.zip', 'MAME'),
    'MAME_wrong_title'    : ('MAME invalid game', 'mjhyewqr.zip', 'MAME'),
    'MAME_wrong_platform' : ('Tetris (set 1)', 'atetris.zip', 'mjhyewqr'),
}

scraper_mobygames_apikey = os.getenv('MOBY_KEY')

def get_setting(key:str):
    if key == 'scraper_cache_dir': return Test_mobygames_metadata_and_assets.TEST_OUTPUT_DIR
    if key == 'scraper_mobygames_apikey': return scraper_mobygames_apikey   
    return ''

class Test_mobygames_metadata_and_assets(unittest.TestCase):
    
    ROOT_DIR = ''
    TEST_DIR = ''
    TEST_OUTPUT_DIR = ''
    TEST_ASSETS_DIR = ''

    @classmethod
    def setUpClass(cls):        
        cls.TEST_DIR = os.path.dirname(os.path.abspath(__file__))
        cls.ROOT_DIR = os.path.abspath(os.path.join(cls.TEST_DIR, os.pardir))
        cls.TEST_ASSETS_DIR = os.path.abspath(os.path.join(cls.TEST_DIR,'assets/'))
        cls.TEST_OUTPUT_DIR = os.path.abspath(os.path.join(cls.TEST_DIR,'output/'))

        if not os.path.exists(cls.TEST_OUTPUT_DIR):
            os.makedirs(cls.TEST_OUTPUT_DIR)
    
    @unittest.skip('You must have an API key to use this resource')
    @patch('resources.lib.scraper.settings.getSetting', autospec=True, side_effect=get_setting)
    def test_mobygames_metadata(self, settings_mock):     
        # --- main ---------------------------------------------------------------------------------------
        print('*** Fetching candidate game list ********************************************************')

        # --- Create scraper object ---
        scraper_obj = MobyGames()
        scraper_obj.set_verbose_mode(False)
        scraper_obj.set_debug_file_dump(True, self.TEST_OUTPUT_DIR)
        status_dic = kodi.new_status_dic('Scraper test was OK')

        # --- Choose data for testing ---
        # search_term, rombase, platform = common.games['metroid']
        # search_term, rombase, platform = common.games['mworld']
        #search_term, rombase, platform = common.games['sonic_megaDrive']
        #search_term, rombase, platform = games['sonic_genesis'] # Aliased platform
        # search_term, rombase, platform = common.games['chakan']
        # search_term, rombase, platform = common.games['console_wrong_title']
        # search_term, rombase, platform = common.games['console_wrong_platform']
        # search_term, rombase, platform = ('Sniper Elite III', 'Sniper.exe', 'Microsoft Windows')
        # search_term, rombase, platform = ('Call of Juarez: Gunslinger', 'juarez.exe', 'Microsoft Windows')
        # :search_term, rombase, platform = ('Planet Coaster', 'coaster.exe', 'Microsoft Windows')
        # search_term, rombase, platform = ('Call of duty: World at war', 'cod.exe', 'Microsoft Windows')
        #search_term, rombase, platform = ('Call of duty: World at war', 'cod.exe', 'Sony PlayStation 3')
        #search_term, rombase, platform = ('Grand Theft Auto V', 'gta.exe', 'Microsoft Windows')
        search_term, rombase, platform = ('Castlevania', 'castlevanio.nes', 'Nintendo NES')

        subject = ROMObj({
            'id': '1234',
            'scanned_data': {
                'identifier': search_term,
                'file': f'/roms/{rombase}'
            },
            'platform': platform,
            'assets': {key: '' for key in constants.ROM_ASSET_ID_LIST},
            'asset_paths': {
                constants.ASSET_TITLE_ID: '/titles/',
            }
        })

        # --- Get candidates, print them and set first candidate ---
        rom_FN = io.FileName(rombase)
        if scraper_obj.check_candidates_cache(rom_FN.getBase(), platform):
            print('>>>> Game "{}" "{}" in disk cache.'.format(rom_FN.getBase(), platform))
        else:
            print('>>>> Game "{}" "{}" not in disk cache.'.format(rom_FN.getBase(), platform))
            
        candidate_list = scraper_obj.get_candidates(search_term, subject, platform, status_dic)
        # pprint.pprint(candidate_list)
        self.assertTrue(status_dic['status'], 'Status error "{}"'.format(status_dic['msg']))
        self.assertIsNotNone(candidate_list, 'Error/exception in get_candidates()')
        self.assertNotEquals(len(candidate_list), 0, 'No candidates found.')
        
        for candidate in candidate_list:
            print(candidate)
        scraper_obj.set_candidate(rom_FN.getBase(), platform, candidate_list[0])
            
        # --- Print metadata of first candidate ----------------------------------------------------------
        print('*** Fetching game metadata **************************************************************')
        metadata = scraper_obj.get_metadata(status_dic)
        # pprint.pprint(metadata)
        print(metadata)
        scraper_obj.flush_disk_cache()

    @unittest.skip('You must have an API key to use this resource')
    @patch('resources.lib.scraper.settings.getSetting', autospec=True, side_effect=get_setting)
    def test_mobygames_assets(self, settings_mock):                 
        # --- main ---------------------------------------------------------------------------------------
        print('*** Fetching candidate game list ********************************************************')

        # --- Create scraper object ---
        scraper_obj = MobyGames()
        scraper_obj.set_verbose_mode(False)
        scraper_obj.set_debug_file_dump(True, self.TEST_OUTPUT_DIR)
        status_dic = kodi.new_status_dic('Scraper test was OK')

        # --- Choose data for testing ---
        # search_term, rombase, platform = common.games['metroid']
        # search_term, rombase, platform = common.games['mworld']
        #search_term, rombase, platform = common.games['sonic_megaDrive']
        search_term, rombase, platform = games['sonic_genesis'] # Aliased platform
        # search_term, rombase, platform = common.games['chakan']
        # search_term, rombase, platform = common.games['console_wrong_title']
        # search_term, rombase, platform = common.games['console_wrong_platform']

        subject = ROMObj({
            'id': '1234',
            'scanned_data': {
                'identifier': search_term,
                'file': f'/roms/{rombase}'
            },
            'platform': platform,
            'assets': {key: '' for key in constants.ROM_ASSET_ID_LIST},
            'asset_paths': {
                constants.ASSET_TITLE_ID: '/titles/',
            }
        })

        # --- Get candidates, print them and set first candidate ---
        rom_FN = io.FileName(rombase)
        if scraper_obj.check_candidates_cache(rom_FN.getBase(), platform):
            print('>>>> Game "{}" "{}" in disk cache.'.format(rom_FN.getBase(), platform))
        else:
            print('>>>> Game "{}" "{}" not in disk cache.'.format(rom_FN.getBase(), platform))
        candidate_list = scraper_obj.get_candidates(search_term, subject, platform, status_dic)
        # pprint.pprint(candidate_list)
        self.assertTrue(status_dic['status'], 'Status error "{}"'.format(status_dic['msg']))
        self.assertIsNotNone(candidate_list, 'Error/exception in get_candidates()')
        self.assertNotEquals(len(candidate_list), 0, 'No candidates found.')
        
        for candidate in candidate_list:
            print(candidate)
            
        scraper_obj.set_candidate(rom_FN.getBase(), platform, candidate_list[0])

        # --- Print list of assets found -----------------------------------------------------------------
        print('*** Fetching game assets ****************************************************************')
        # --- Get specific assets ---
        self.print_game_assets(scraper_obj.get_assets(constants.ASSET_TITLE_ID, status_dic))
        self.print_game_assets(scraper_obj.get_assets(constants.ASSET_SNAP_ID, status_dic))
        self.print_game_assets(scraper_obj.get_assets(constants.ASSET_BOXFRONT_ID, status_dic))
        self.print_game_assets(scraper_obj.get_assets(constants.ASSET_BOXBACK_ID, status_dic))
        self.print_game_assets(scraper_obj.get_assets(constants.ASSET_CARTRIDGE_ID, status_dic))
        scraper_obj.flush_disk_cache()

    def print_game_assets(self, assets):
        for asset in assets:
            print(asset)