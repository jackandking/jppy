# -*- coding: utf-8 -*-
# Author: Yingjie.Liu@thomsonreuters.com
# DateTime: 2013-09-30 20:42:42.956000
# Generator: https://github.com/jackandking/newpy
# Newpy Version: 1.1
# Newpy ID: 155
# Description: I'm a lazy person, so you have to figure out the function of this script by yourself.

import unittest
from filecache import FileCache
import re
import logging
logging.basicConfig(format='%(levelname)s:%(message)s',level=logging.DEBUG)

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

class _HTML_UT(unittest.TestCase):
  def test1(self):
    import urllib2
    l_url='http://www.52zhongtou.com'
    l_fidlist=[FID('Title', ReadRule('<title>(.*?)</title>'))]
    l_fc=FileCache(lambda a_url:urllib2.urlopen(a_url).read())
    l_h=HTML(l_url,l_fidlist,l_fc)
    l_h.fetch()
    l_h.parse()

def main():
  unittest.main(verbosity=2)

if __name__ == '__main__':
  main()
