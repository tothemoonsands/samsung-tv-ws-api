#!/usr/bin/env python3
# web frontend for gallery display
# please install flask with the async option (pip install flask[async])
# and bootstrap-flask (pip install Bootstrap-Flask)
# V 1.0.0 14/3/25 NW Initial release
# V 1.0.1 15/3/25 NW Added |safe filter in modal Marco for description and details
# V 1.1.1 18/3/25 NW updated to load modal dialog on demand

import asyncio
from flask import Flask, Response, jsonify, redirect, request, url_for, render_template, get_template_attribute
from flask_bootstrap import Bootstrap5
from pathlib import Path
import argparse, os, time
import logging

from async_art_gallery_web import monitor_and_display

__version__ = '1.1.1'
data = {}

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
    parser.add_argument('-d','--display_for', action="store", type=int, default=120, help='how long to display manually selected art for (default: %(default)s))')
    parser.add_argument('-mo','--modal', default='', choices=['modal-sm', 'modal-lg', 'modal-xl', 'modal-fullscreen', 'modal-fullscreen-sm-down',
                                                              'modal-fullscreen-md-down', 'modal-fullscreen-lg-down', 'modal-fullscreen-xl-down', 'modal-fullscreen-xxl-down'],
                                         help='size of modal text box see https://www.w3schools.com/bootstrap5/bootstrap_modal.php for explanation (default: medium')
    parser.add_argument('-s','--sync', action='store_false', default=True, help='automatically syncronize (needs Pil library) (default: %(default)s))')
    parser.add_argument('-K','--kiosk', action='store_true', default=False, help='Show in Kiosk mode (default: %(default)s))')
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
    mon.display_file(name)
    return {}, 200
    
@app.route("/modal/<file>")
def show_modal(file):
    '''
    build html for bootstrap modal from template
    '''
    text = get_text(file)
    modal_window = get_template_attribute('macros.html', 'render_modal')
    return modal_window(text, args.modal)
    
@app.route('/SSE')
def SSE():
    '''
    stream currently shown image id
    '''
    return Response(stream(), mimetype='text/event-stream')
    
def stream():
    log.info('starting stream')
    try:
        filename = mon.wait_for_filename_change()  # filename change generator
        while True:
            file = next(filename)  # blocks until a new filename arrives
            yield format_sse(file)
    except Exception as e:
        log.warning('stream exited: {}'.format(e))
    
def format_sse(data, event='message'):
    log.info('sending event: {} data: {}'.format(event, data))
    return 'event: {}\ndata: {}\n\n'.format(event, data)

@app.route('/')    
def show_thumbnails():
    '''
    construct thumbnail page, and load all text data
    pass to template as a dictionary
    '''
    global data
    log.info('loading thumnail page')
    image_names = [img for img in os.listdir(app.static_folder) if not img.upper().endswith('.TXT')]
    log.info('displaying Buttons for: {}'.format(image_names))
    return render_template('home.html', names=image_names, kiosk=str(args.kiosk).lower())
    
def get_text(file):
    '''
    takes a image file name and numerical id, changes the extension to TXT, reads the file from the static folder
    and returns a dictionary of the json
    returns the default values if file not found
    '''
    #default info
    data = {"id": Path(file).with_suffix(""), "name": file, "header": "Wildlife Scene", "details": "A dramatic landscape"}
    text_file = os.path.join(app.static_folder, Path(file).with_suffix(".TXT"))   
    try:
        with open(text_file, 'r') as f:
            text = app.json.load(f)
        log.debug('got text for image: {}: {}'.format(file, text))
        data.update(text)
    except Exception as e:
        log.warning('error: {}: {}'.format(e, text_file))
    return data
    
def run(args):
    app.static_folder = args.folder
    log.info('Serving files from: {}'.format(app.static_folder))
    app.run(host='0.0.0.0', port=args.port, debug=args.debug, use_reloader=False, threaded=True)
        
async def main():
    global log
    global mon
    global args
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
        
    if args.kiosk:
        log.info("Running in Kiosk mode")

    mon = monitor_and_display(  args.ip,
                                args.folder,
                                period          = args.check,
                                update_time     = args.update,
                                display_for     = args.display_for,
                                include_fav     = args.favourite,
                                sync            = args.sync,
                                matte           = args.matte,
                                sequential      = args.sequential,
                                on              = args.on,
                                token_file      = args.token_file)
                                
    web = asyncio.to_thread(run, args)
    web_task = asyncio.create_task(web)
    #await asyncio.sleep(5)
    if not web_task.done():
        await mon.start_monitoring()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        os._exit(1)    

