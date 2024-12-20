#!/usr/bin/env python3
import argparse
import logging
import os
import sys

sys.path.append("../")

from samsungtvws import SamsungTVWS, exceptions, __version__

def parseargs():
    # Add command line argument parsing
    parser = argparse.ArgumentParser(description='Example art Samsung Frame TV Version: {}'.format(__version__))
    parser.add_argument('ip', action="store", type=str, default=None, help='ip address of TV (default: %(default)s))')
    parser.add_argument('-t','--token_file', action="store", type=str, default="token_file.txt", help='default token file to use (default: %(default)s))')
    parser.add_argument('-D','--debug', action='store_true', default=False, help='Debug mode (default: %(default)s))')
    return parser.parse_args()
    
class Slideshow:
    input_chars = ['n', 'p']
    
    def __init__(self, args):
        self.log = logging.getLogger('Main.'+__class__.__name__)
        # Normal constructor (will ask for connection every time on 2024 TV's)
        self.tv = SamsungTVWS(host=args.ip, port=8002)
        
        # Autosave token to file
        #self.tv = SamsungTVWS(host=args.ip, port=8002, token_file=args.token_file)
        self.sequence = self.get_tv_content()
        self.current = self.get_current_art()
        try:
            self.index = self.sequence.index(self.current)
            self.input_loop()
        except ValueError as e:
            self.log.critical('Current art not found: {}'.format(e))
        
    def input_loop(self):
        '''
        gets next character from keyboard
        n = next, p = previous, q = quit
        '''
        char = None
        while char != 'q' :
            char = input('n,p,q >> ').lower()
            if char in self.input_chars:
                self.advance_frame_image(char)
        
    def get_tv_content(self, category='MY-C0002'):
        '''
        gets content_id list of category - either My Photos (MY-C0002) or Favourites (MY-C0004) from tv
        use 10 second timeout in case tv has a lot of content (tv.art(10))
        '''
        try:
            result = [v['content_id'] for v in self.tv.art().available(category)]
        except AssertionError:
            self.log.warning('failed to get contents from TV')
            result = None
        return result
        
    def get_current_art(self):
        '''
        gets content_id for current art
        '''
        try:
            art = self.tv.art().get_current()
            result = art['content_id']
        except AssertionError:
            self.log.warning('failed to get current art from TV')
            result = None
        return result
        
    def advance_frame_image(self, char='n'):
        '''
        Next or previous image in the sequence
        '''
        try:
            new_index = self.index+1 if char == 'n' else self.index-1
            # wrap around
            new_index = new_index % len(self.sequence)
            self.log.info('current index: {} new index: {} max: {}'.format(self.index, new_index, len(self.sequence)-1))
            next_id = self.sequence[new_index]
            # Select new image
            self.tv.art().select_image(next_id)
            self.log.info(f"Advanced from {self.sequence[self.index]} to {next_id}")
            self.index = new_index
            return True
            
        except Exception as e:
            self.log.error(f"Error changing image: {e}")
            return False

def main():
    args = parseargs()
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s',
                        level=logging.DEBUG if args.debug else logging.INFO)
    logging.debug('debug mode')
    Slideshow(args)


if __name__ == '__main__':
    main()