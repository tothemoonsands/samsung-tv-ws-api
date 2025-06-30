#!/usr/bin/env python3
# fully async example program to slideshow any art on Frame TV

'''
Instructions:
Start the program with tv ip and -u set to however many minutes you want for the slideshow period
A 'slideshow' folder will be created, whith two sub folders 'my_photos' and 'favourites'
The 'my_photos' and 'favourites' will be syncronized with the TV folders every 60 seconds.
Do not put any other files in these folders, as they will be deleted. Add or remove from them using the smarthings app,
and wait for the folder to syncronize.
The 'slideshow' folder will initially be populated with the contents of the 'favourites' folder on first run, or if you delete all the files.

To choose what artwork to be displayed in the slideshow, COPY files from 'favourites' or 'my_photos' to 'slideshow'
Any artwork you don't want to be in the slideshow, delete from the 'slideshow' folder.
If you delete files from your TV, or un-favourite them, the corresponding files will be deleted from 'slideshows' (if present)

Only artwork in the 'slideshow' folder will be shown on the TV.

The sequence is random, and the time period will resume automatically when the program is restarted
'''

import logging
import os
import shutil
import random
import asyncio
import time
import argparse
import datetime
from signal import SIGTERM, SIGINT
from dataclasses import dataclass
from enum import Enum

from samsungtvws.async_art import SamsungTVAsyncArt
from samsungtvws import __version__

logging.basicConfig(level=logging.INFO)


def parseargs():
    # Add command line argument parsing
    parser = argparse.ArgumentParser(description='Async Slideshow Any art on Samsung TV Version: {}'.format(__version__))
    parser.add_argument(
        'ip',
        nargs='?',
        default=os.environ.get('TV_IP'),
        help='ip address of TV (default: env TV_IP)'
    )
    parser.add_argument('-f','--folder', action="store", type=str, default="./slideshow", help='folder to store images in (default: %(default)s))')
    parser.add_argument('-t','--token_file', action="store", type=str, default="token_file.txt", help='default token file to use (default: %(default)s))')
    parser.add_argument('-c','--check', action="store", type=int, default=60, help='how often to check for new art 0=run once (default: %(default)s))')
    parser.add_argument('-u','--update', action="store", type=float, default=2, help='random update period (mins) 0.25 minnimum (default: %(default)s))')
    parser.add_argument('-D','--debug', action='store_true', default=False, help='Debug mode (default: %(default)s))')
    return parser.parse_args()
    
@dataclass
class artDataMixin:
    dir_name:str
    category_id: str
    dir: str
    tv_files: set()
    
class slideshow:

    category = Enum(
        value="categories",
        names=[ ("MY_PHOTOS",  ('my_photos', 'MY-C0002', None, set())),
                ("FAVOURITES", ('favourites', 'MY-C0004', None, set())),
                ("SLIDESHOW",  ('slideshow', None, None, set())),
              ],
        type=artDataMixin,
    )
    
    def __init__(self, ip, folder, period=60, random_update=1440, token_file=None):
        self.log = logging.getLogger('Main.'+__class__.__name__)
        self.debug = self.log.getEffectiveLevel() <= logging.DEBUG
        self.ip = ip
        self.random_update = max(0.25, random_update)*60   #convert minutes to seconds
        self.period = int(min(60, self.random_update)) if period else 0
        # Autosave token to file
        self.token_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), token_file) if token_file else token_file
        self.category.SLIDESHOW.dir = folder
        self.category.MY_PHOTOS.dir = os.path.join(folder, self.category.MY_PHOTOS.dir_name)
        self.category.FAVOURITES.dir = os.path.join(folder, self.category.FAVOURITES.dir_name)
        self.api_version = 1
        self.start = time.time()
        self.tv = SamsungTVAsyncArt(host=self.ip, port=8002, token_file=self.token_file)
        
        self.log.info('check thumbnails {}, slideshow rotation every: {}'.format('every {}s'.format(self.period) if self.period else 'once', datetime.timedelta(seconds = self.random_update)))
        try:
            #doesn't work in Windows
            asyncio.get_running_loop().add_signal_handler(SIGINT, self.close)
            asyncio.get_running_loop().add_signal_handler(SIGTERM, self.close)
        except Exception:
            pass
        
    async def start_slideshow(self):
        await self.tv.start_listening()
        await self.select_artwork()
        await self.tv.close()
        
    def close(self):
        self.log.info('SIGINT/SIGTERM received, exiting')
        os._exit(1)
        
    def make_directory(self, directory):
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as e:
            pass
        
    async def get_api_version(self):
        api_version = await self.tv.get_api_version()
        self.api_version = 0 if int(api_version.replace('.','')) < 4000 else 1
        
    async def get_tv_content(self, category='MY-C0002'):
        result = []
        try:
            result = [v['content_id'] for v in await self.tv.available(category, timeout=10)]
        except AssertionError:
            pass
        return result
        
    async def get_thumbnails(self, content_ids):
        thumbnails = {}
        if content_ids:
            if self.api_version == 0:
                if len(content_ids) > 10:
                    self.log.info('This may take a few minutes...')
                thumbnails = await self.tv.get_thumbnail(content_ids, True)
            elif self.api_version == 1:
                thumbnails = await self.tv.get_thumbnail_list(content_ids)
        self.log.info('got {} thumbnails'.format(len(thumbnails)))
        return thumbnails
        
    async def initialize(self):
        for cat in self.category:
            self.make_directory(cat.dir)
        await self.get_api_version()
        await self.download_thmbnails()
        if not self.get_files(self.category.SLIDESHOW):
            self.log.info('initializing slideshow from favourites')
            for file in self.get_files(self.category.FAVOURITES):
                shutil.copy2(os.path.join(self.category.FAVOURITES.dir, file), self.category.SLIDESHOW.dir)
        await self.set_start()
                
    async def set_start(self):
        content_id = (await self.tv.get_current()).get('content_id')
        self.log.debug('got current artwork: {}'.format(content_id))
        self.start = max(time.time() - self.random_update*60, self.get_last_updated(self.get_filename(content_id, self.category.SLIDESHOW)))
              
    def get_files(self, cat):
        return self.get_file_set(cat.dir)
        
    def get_filename(self, content_id, cat):
        return next(iter(f for f in self.get_files(cat) if self.get_content_ids(f) == content_id), None)
        
    def get_last_updated(self, filename):
        if filename:
            return os.path.getmtime(os.path.join(self.category.SLIDESHOW.dir, filename))
        return time.time()
        
    def set_last_updated(self, filename):
        if filename:
            path = os.path.join(self.category.SLIDESHOW.dir, filename)
            os.utime(path, (os.path.getctime(path), time.time()))
        
    async def update_thmbnails(self, cat):
        self.log.info('checking thumbnails {}'.format(cat.name))
        files = self.get_files(cat)
        cat.tv_files = set(await self.get_tv_content(cat.category_id))
        self.log.debug('got content list: {}'.format(cat.tv_files))
        new_thumbnails = cat.tv_files.difference(self.get_content_ids(files))
        self.log.info('downloading {} thumbnails'.format(len(new_thumbnails)))
        if new_thumbnails:
            photos_thumbnails = await self.get_thumbnails(new_thumbnails)
            new_thumbnails = {k:v for k,v  in photos_thumbnails.items() if k not in files}
            self.write_thumbnails(cat.dir, new_thumbnails) 
            
    def remove_files(self, cat):
        self.log.info('checking for deleted files in {}'.format(cat.dir))
        files = self.get_files(cat)
        if cat == self.category.SLIDESHOW:
            my_files_remove = self.get_content_ids(files).difference(self.category.MY_PHOTOS.tv_files.union(self.category.FAVOURITES.tv_files))
        else:
            my_files_remove = self.get_content_ids(files).difference(cat.tv_files)
        remove_files = [os.path.join(cat.dir, f) for f in files if self.get_content_ids(f) in my_files_remove]
        self.log.debug('photos to remove: {}'.format(my_files_remove))
        self.log.info('removing: {}'.format(remove_files))
        for path in remove_files:
            if os.path.exists(path):
                self.log.debug('deleting file: {}'.format(path))
                os.unlink(path)
            else:
                self.log.warning('cannot remove {} as it does not exist'.format(path))
        self.log.info('done checking for deleted files')
        
    async def download_thmbnails(self):
        await self.update_thmbnails(self.category.MY_PHOTOS)
        await self.update_thmbnails(self.category.FAVOURITES)
        self.remove_files(self.category.MY_PHOTOS)
        self.remove_files(self.category.FAVOURITES)
        self.remove_files(self.category.SLIDESHOW)
        
    async def do_random_update(self):
        if time.time() - self.start > self.random_update:
            self.log.info('doing random update, after {}'.format(datetime.timedelta(seconds = self.random_update)))
            self.start = time.time()
            await self.download_thmbnails()
            slideshow_files = list(self.get_content_ids(self.get_files(self.category.SLIDESHOW)))
            if slideshow_files:
                content_id = random.choice(slideshow_files)
                self.log.info('selecting tv art: content_id: {}'.format(content_id))
                self.set_last_updated(self.get_filename(content_id, self.category.SLIDESHOW))
                await self.tv.select_image(content_id)
            return True
        return False
            
    def write_thumbnails(self, folder, thumbnails):
        try:
            for filename, data in thumbnails.items():
                path = os.path.join(folder, filename)
                if not os.path.exists(path):
                    self.log.info('writing {}'.format(path))
                    with open(path, 'wb') as f:
                        f.write(data)
        except Exception as e:
            self.log.error('error writing file: {}, {}'.format(os.path.join(folder, filename), e))
        
    def get_file_set(self, folder):
        return {f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))}
            
    def get_content_ids(self, filenames):
        if isinstance(filenames, str):
            return os.path.splitext(filenames)[0]
        return {os.path.splitext(v)[0] for v in filenames}
        
    def get_countdown(self):
        return datetime.timedelta(seconds = max(0, (self.random_update - (time.time() - self.start))))

    async def select_artwork(self):
        await self.initialize()
        start = True
        while True:
            try:
                if await self.tv.in_artmode():
                    self.log.info('time to next rotation: {}'.format(self.get_countdown()))
                    if not await self.do_random_update() and not start:
                        await self.download_thmbnails()
                    start = False
                else:
                    self.log.info('artmode or tv is off')
            except Exception as e:
                self.log.warning("error in select_artwork: {}".format(e))
                if self.debug:
                    self.log.exception(e)
            if self.period == 0:
                break
            await asyncio.sleep(self.period)
            
async def main():
    global log
    log = logging.getLogger('Main')
    args = parseargs()
    if args.debug:
        log.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
    log.debug('Debug mode')
    
    mon = slideshow(args.ip,
                    os.path.normpath(args.folder),
                    period          = args.check,
                    random_update   = args.update,
                    token_file      = args.token_file)
    await mon.start_slideshow()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        os._exit(1)