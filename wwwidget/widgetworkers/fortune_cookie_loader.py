#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import logging
import logging.config

# create logger
logger = logging.getLogger(__name__)

class fortune_cookie_loader(object):
    def __init__(self, fortune_file, max_width = None, max_height = None, search_word = None):
        self.found_fortune_cookies = []
        valid_cookies = 0
        all_cookies = 0
        with open(fortune_file) as file_in:
            current_fortune_cookie = []
            for line in file_in:
                line = line.strip()
                if line == '%':
                    all_cookies += 1
                    if self.is_fortune_cookie_valid(current_fortune_cookie, max_width, max_height, search_word):
                        valid_cookies += 1
                        self.found_fortune_cookies.append(current_fortune_cookie)
                    current_fortune_cookie = []
                else:
                    current_fortune_cookie.append(line)
        
        logger.debug("Done. {}/{} Fortune Cookies loaded".format(valid_cookies, all_cookies))
        
    def is_fortune_cookie_valid(self, fortune_cookie, max_width = None, max_height = None, search_word = None):
        if max_height:
            if len(fortune_cookie) > max_height:
                return False
        
        if max_width:
            if any(len(line)>max_width for line in fortune_cookie):
                return False
        
        if search_word:
            if all((search_word not in line) for line in fortune_cookie):
                return False
        
        return True
        
    def return_fortune_cookie(self):
        return random.choice(self.found_fortune_cookies)
    
    
    
def main():
    f = fortune_cookie_loader("/usr/share/games/fortunes/songs-poems", search_word="Moon")
    print(f.return_fortune_cookie())
    print("---")
    
    
#main()