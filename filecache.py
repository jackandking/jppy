# -*- coding: utf-8 -*-
# Author: Yingjie.Liu@thomsonreuters.com
# DateTime: 2013-09-30 20:24:09.233000
# Generator: https://github.com/jackandking/newpy
# Newpy Version: 1.1
# Newpy ID: 154
# Description: I'm a lazy person, so you have to figure out the function of this script by yourself.

import unittest
import hashlib
import os
import logging
logging.basicConfig(format='%(levelname)s:%(message)s',level=logging.DEBUG)

class FileCache:
  def __init__(self,a_fetch_func):
    self.m_fetch_func=a_fetch_func
  def get(self,a_uri):
    l_m=hashlib.md5(a_uri)
    l_filename=l_m.hexdigest() + '.html'
    if os.path.isfile(l_filename):
      logging.info('Read cached file<%s> for URI<%s>',l_filename ,a_uri)
      l_content=open(l_filename,'rb').read()
    else:
      logging.info('Fetch URI<%s> and cache to file<%s>',a_uri,l_filename)
      l_content = self.m_fetch_func(a_uri)
      l_file=open(l_filename,'wb')
      l_file.write(l_content)
      l_file.close()
    return l_content

class _FileCache_UT(unittest.TestCase):
  def test1(self):
    import urllib2
    l_fc=FileCache(lambda a_url:urllib2.urlopen(a_url).read())
    l_fc.get('http://www.baidu.com')

def main():
  unittest.main(verbosity=2)

if __name__ == '__main__':
  main()
