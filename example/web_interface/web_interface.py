#!/usr/bin/env python3
# web frontend for gallery display
# please install flask with the async option (pip install flask[async])
# and bootstrap-flask (pip install Bootstrap-Flask)

import asyncio
from flask import Flask, Response, jsonify, redirect, request, url_for, render_template
from flask_bootstrap import Bootstrap5
from pathlib import Path
import argparse, os, json
import logging

__version__ = '0.0.1'

from async_art_gallery_web import monitor_and_display

logging.basicConfig(level=logging.INFO)

def parseargs():
    # Add command line argument parsing
    parser = argparse.ArgumentParser(description='Async Upload images to Samsung TV Version: {}'.format(__version__))
    parser.add_argument('ip', action="store", type=str, default=None, help='ip address of TV (default: %(default)s))')
    parser.add_argument('-p','--port', action="store", type=int, default=5000, help='port for web page interface (default: %(default)s))')
    parser.add_argument('-f','--folder', action="store", type=str, default="./images", help='folder to load images from (default: %(default)s))')
    parser.add_argument('-m','--matte', action="store", type=str, default="none", help='default matte to use (default: %(default)s))')
    parser.add_argument('-t','--token_file', action="store", type=str, default="token_file.txt", help='default token file to use (default: %(default)s))')
    parser.add_argument('-u','--update', action="store", type=float, default=0, help='slideshow update period (mins) 0=off (default: %(default)s))')
    parser.add_argument('-c','--check', action="store", type=int, default=600, help='how often to check for new art 0=run once (default: %(default)s))')
    parser.add_argument('-s','--sync', action='store_false', default=True, help='automatically syncronize (needs Pil library) (default: %(default)s))')
    parser.add_argument('-S','--sequential', action='store_true', default=False, help='sequential slide show (default: %(default)s))')
    parser.add_argument('-O','--on', action='store_true', default=False, help='exit if TV is off (default: %(default)s))')
    parser.add_argument('-F','--favourite', action='store_true', default=False, help='include favourites in rotation (default: %(default)s))')
    parser.add_argument('-D','--debug', action='store_true', default=False, help='Debug mode (default: %(default)s))')
    return parser.parse_args()

app = Flask(__name__)
bootstrap = Bootstrap5(app)

@app.route('/show_image/<name>')
def show_image(name):
    '''
    add image selected to queue for gallery display on TV
    '''
    log.info('show image: {}'.format(name))
    mon.add_to_queue(name)
    return jsonify()

@app.route('/')    
def show_thumbnails():
    '''
    construct thumbnail page, and load all text data
    pass to template as a disctionary
    '''
    log.info('loading thumnail page')
    data = {}
    image_names = [img for img in os.listdir(app._static_folder) if not img.upper().endswith('.TXT')]
    for id, file in enumerate(image_names):
        #default info
        data[file] = {"id": id,"header": "Wildlife Scene", "details": "A dramatic landscape"}
        text_file = os.path.join(app._static_folder, Path(file).with_suffix(".TXT"))
        try:
            with open(text_file, 'r') as f:
                text = json.load(f)
            log.debug('got text for image: {}: {}'.format(file, text))
            data[file].update(text)
        except Exception as e:
            log.warning('error: {}: {}'.format(e, text_file))
        
    log.info('displaying: {}'.format(list(data.keys())))
    return render_template('home.html', data=data)
    
def run(args):
    app._static_folder = args.folder
    app.run(host='0.0.0.0', port=args.port, debug=args.debug, use_reloader=False)
        
async def main():
    global log
    global mon
    args = parseargs()
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s',
                        force=True,
                        level=logging.DEBUG if args.debug else logging.INFO)
    log = logging.getLogger('Main')
    log.info('Program Started, version: {}'.format(__version__))
    log.debug('Debug mode')
    
    args.folder = os.path.normpath(args.folder)
    
    if not os.path.exists(args.folder):
        self.log.warning('folder {} does not exist, exiting'.format(args.folder))
        os._exit(1)

    mon = monitor_and_display(  args.ip,
                                args.folder,
                                period          = args.check,
                                update_time     = args.update,
                                include_fav     = args.favourite,
                                sync            = args.sync,
                                matte           = args.matte,
                                sequential      = args.sequential,
                                on              = args.on,
                                token_file      = args.token_file)
                                
    web = asyncio.to_thread(run, args)
    web_task = asyncio.create_task(web)
    await asyncio.sleep(5)
    if not web_task.done():
        await mon.start_monitoring()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        os._exit(1)    

