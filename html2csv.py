# -*- coding: utf-8 -*-
# Author: Yingjie.Liu@thomsonreuters.com
# DateTime: 2013-09-12 17:22:10.660000
# Generator: https://github.com/jackandking/newpy
# Newpy Version: 0.8
# Newpy ID: 85
# Description: use it to fetch patterned FID from webpage and save to csv file per FID-specific rules.

import urllib2
import re
import pdb
import unicodecsv as csv
import unittest
import inspect
import logging
logging.basicConfig(format='%(levelname)s:%(message)s',level=logging.DEBUG)

import hashlib
import os
class FileCache:
  def __init__(self,a_fetch_func):
    self.m_fetch_func=a_fetch_func
  def get(self,a_uri):
    l_m=hashlib.md5(a_uri)
    l_filename=l_m.hexdigest() + '.html'
    if os.path.isfile(l_filename):
      logging.info('Read cached file<%s> for URI<%s>',l_filename ,a_uri)
      l_content=open(l_filename,'r').read()
    else:
      logging.info('Fetch URI<%s> and cache to file<%s>',a_uri,l_filename)
      l_content = self.m_fetch_func(a_uri)
      l_file=open(l_filename,'wb')
      l_file.write(l_content)
      l_file.close()
    return l_content
    
class HTML:
  def __init__(self,a_url,a_fid_list,a_fcache=None):
    self.m_url=a_url
    self.m_fid_list=a_fid_list
    self.m_content=None
    self.m_fiddata_list=[]
    self.m_fcache=a_fcache

  def fetch(self):
    try:
      if self.m_fcache:
        self.m_content=self.m_fcache.get(self.m_url)
      else:
        self.m_content=urllib2.urlopen(self.m_url).read()
      if self.m_content is None:
        raise Exception("get nothing!")
    except Exception,e:
      raise Exception("Fetch error with URL("+self.m_url+")."+str(e))
    except:
      raise Exception("Fetch error with URL("+self.m_url+").")
    return self

  def parse(self):
    try:
      for l_fid in self.m_fid_list:
        l_fiddata=FIDData(l_fid)
        l_fiddata.read(self.m_content)
        self.m_fiddata_list.append(l_fiddata)
    except Exception,e:
      raise Exception("URL("+self.m_url+")."+str(e))
    return self

class CSV(object):
  def __init__(self,filename):
    self.m_filename=filename
    self.m_url_list=[]
    self.m_fid_list=[]
    self.m_row_list=[]
    self.m_debug=None
  def debug_mode(self,a_trigger):
    self.m_debug=a_trigger
  def add_url(self,a_url):
    logging.debug('add_url %s',a_url)
    self.m_url_list.append(a_url)
    return self
  def add_fid(self,a_fid):
    self.m_fid_list.append(a_fid)
    return self
  def fetch(self):
    l_fcache=None
    if self.m_debug:
      logging.debug('in debug mode so use cache')
      l_fcache=FileCache(lambda a_url:urllib2.urlopen(a_url).read())
    for l_url in self.m_url_list:
      logging.debug('fetching %s',l_url)

      l_html=HTML(l_url,self.m_fid_list,l_fcache)
      l_html.fetch()
      l_html.parse()
      self.m_row_list.append(l_html.m_fiddata_list)

  def write(self):

    for l_row in self.m_row_list:
      for l_fiddata in l_row:
        l_fiddata.write(l_row)

    l_csv=open(self.m_filename,'wb')
    l_writer=csv.writer(l_csv, encoding='utf8')

    l_header_row=[]
    for l_fid in self.m_fid_list:
      l_header_row.append(l_fid.m_name)
    l_writer.writerow(l_header_row)

    for l_row in self.m_row_list:
      logging.debug("write one more row")
      l_data_row=[]
      for l_fiddata in l_row:
        logging.debug("write one more cell <%s>",l_fiddata.m_value)
        l_data_row.append(l_fiddata.m_value)
      l_writer.writerow(l_data_row)

    l_csv.close()
    return True

class Rule:
  def set_name(self, name):
    self.m_name=name

class ReadRule(Rule):
  def __init__(self, pattern):
    self.m_pattern=pattern
  def apply_read(self, a_input,a_fiddata):
    if self.m_pattern is None:
      return True
    
    try:
      l_m= re.findall(self.m_pattern, a_input)
      if len(l_m) >1:
        raise Exception("multi-match is not acceptable, please change your readrule for "+self.m_name)
      if len(l_m) <1:
        raise Exception("zero-match is not acceptable, please change your readrule for "+self.m_name)
  ##    pdb.set_trace()
      #a_fiddata.m_value=l_m[0].decode('utf8')
      a_fiddata.m_value=l_m[0]
      logging.debug('read one FID(%s):%s',a_fiddata.m_fid.m_name,a_fiddata.m_value)
    except Exception,e:
      raise Exception("ReadRule("+self.m_pattern+")."+str(e))
    return True

class WriteRule(Rule):
  def __init__(self, a_code=None):
    self.m_code=a_code
  def apply_write(self, a_fiddata_list, a_fiddata):
    if self.m_code is None:
      return True

    l_fidmap={}
    if a_fiddata_list:
      for l_fiddata in a_fiddata_list:
        l_fidmap[l_fiddata.m_fid.m_name]=l_fiddata.m_value

    #define alias names to easy user
    I=a_fiddata.m_value
    FIELD=l_fidmap
    
    exec(self.m_code)

    logging.debug('write one FID(%s):%s -> %s',a_fiddata.m_fid.m_name,a_fiddata.m_value,I)
    a_fiddata.m_value=I
    return True

class FID(object):
  def __init__(self,name,readrule,writerule=WriteRule()):
    self.m_name=name
    self.m_readrule=readrule
    self.m_readrule.set_name(name)
    self.m_writerule=writerule
    self.m_writerule.set_name(name)
  def read(self, a_from, a_to):
    try:
      self.m_readrule.apply_read(a_from,a_to)
    except Exception,e:
      #raise Exception("FID("+self.m_name+")."+"ReadRule("+self.m_readrule.m_pattern.decode("utf8").encode("gb2312")+"): "+str(e))
      raise Exception("FID("+self.m_name+")."+str(e))
  def write(self, a_context, a_to):
    self.m_writerule.apply_write(a_context,a_to)

class FIDData:
  def __init__(self,a_fid):
    self.m_fid=a_fid
    self.m_value=None
  def read(self, a_from):
    self.m_fid.read(a_from,self)
    return self
  def write(self, a_context):
    self.m_fid.write(a_context, self)
    return self

class HTML2CSV(CSV):
  def convert(self):
    self.fetch()
    self.write()
  def add_fid(self,a_name,a_readrule_pattern,a_writerule_code=None):
    return super(HTML2CSV,self).add_fid(FID(a_name,ReadRule(a_readrule_pattern),WriteRule(a_writerule_code)))

class HTML2CSV_UT(unittest.TestCase):

  def test_one_html(self):
    l_filename=inspect.stack()[0][3]+".csv"
    l_csv=CSV(l_filename)
    l_csv.debug_mode(True)
    l_csv.add_url('http://www.52zhongtou.com')
    l_csv.add_fid(FID('Title', ReadRule('<title>(.*?)</title>')))
    l_csv.fetch()
    l_csv.write()
    #l_filecont=open(l_filename).read()
    #print l_filecont.decode('utf8').encode('gb2312')
    self.failUnless(open(l_filename).read() == open(l_filename+".exp").read())


  def test_multi_html(self):
    l_filename=inspect.stack()[0][3]+".csv"
    l_csv=CSV(l_filename)
    l_csv.debug_mode(True)
    l_csv.add_url('http://www.52zhongtou.com/ProjectView/Detail/pid/74')\
        .add_url('http://www.52zhongtou.com/ProjectView/Detail/pid/72')
    l_csv.add_fid(FID('Name', ReadRule('来自.*?>(.*?)</a>')))
    l_csv.fetch()
    l_csv.write()
    self.failUnless(open(l_filename).read() == open(l_filename+".exp").read())

  def test_multi_fid(self):
    l_filename=inspect.stack()[0][3]+".csv"
    l_csv=CSV(l_filename)
    l_csv.debug_mode(True)
    l_csv.add_url('http://www.52zhongtou.com/ProjectView/Detail/pid/74')
    l_csv.add_fid(FID('Name', ReadRule('来自.*?>(.*?)</a>')))
    l_csv.add_fid(FID('Title', ReadRule('<title>(.*?)</title>')))
    l_csv.fetch()
    l_csv.write()
    self.failUnless(open(l_filename).read() == open(l_filename+".exp").read())

  def test_writerule(self):
    l_filename=inspect.stack()[0][3]+".csv"
    l_csv=CSV(l_filename)
    l_csv.debug_mode(True)
    l_csv.add_url('http://www.52zhongtou.com/ProjectView/Detail/pid/74')
    l_csv.add_fid(FID('Name', ReadRule('来自.*?>(.*?)</a>')))
    l_csv.add_fid(FID('Title', ReadRule('<title>(.*?)</title>')))
    l_csv.add_fid(FID('Name_Title', ReadRule(None), 
      WriteRule('''I=FIELD['Name']+FIELD['Title']''')))
    l_csv.fetch()
    l_csv.write()
    self.failUnless(open(l_filename).read() == open(l_filename+".exp").read())

  def test_HTML2CSV(self):
    l_filename=inspect.stack()[0][3]+".csv"
    l_h2c=HTML2CSV(l_filename)
    l_h2c.debug_mode(True)
    l_h2c.add_url('http://www.52zhongtou.com/ProjectView/Detail/pid/74')
    l_h2c.add_fid('Name', '来自.*?>(.*?)</a>')
    l_h2c.add_fid('Title', '<title>(.*?)</title>')
    l_h2c.add_fid('Name_Title', None, '''I=FIELD['Name']+FIELD['Title']''')
    l_h2c.convert()
    self.failUnless(open(l_filename).read() == open(l_filename+".exp").read())

  def test_useHTML2CSVonly(self):
    l_filename=inspect.stack()[0][3]+".csv"
    l_h2c=HTML2CSV(l_filename)
    l_h2c.debug_mode(True)
    l_h2c.add_url('http://www.52zhongtou.com/ProjectView/Detail/pid/74')
    l_h2c.add_fid('Name', '来自.*?>(.*?)</a>')
    l_h2c.add_fid('Name2', None, '''I=FIELD['Name']''')
    l_h2c.convert()
    self.failUnless(open(l_filename).read() == open(l_filename+".exp").read())

def main():
  unittest.main(verbosity=2)

if __name__ == '__main__':
  main()
