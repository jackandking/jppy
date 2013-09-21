# -*- coding: utf-8 -*-
# Author: Yingjie.Liu@thomsonreuters.com
# DateTime: 2013-09-20 22:15:19.875000
# Generator: https://github.com/jackandking/newpy
# Newpy Version: 1.0
# Newpy ID: 142
# Description: firstly fetch urls from given html, then work as HTML2CSV.

from html2csv import *
import unittest
import logging
logging.basicConfig(format='%(levelname)s:%(message)s',level=logging.DEBUG)

class URLReadRule(ReadRule):
  def apply_read(self, a_input, a_fiddata):
    if self.m_pattern is None:
      return True

    try:
      l_m=re.findall(self.m_pattern, a_input)

      if not l_m:
        logging.warning("URLReadRule(%s) got nothing!",self.m_pattern)
        return False

      a_fiddata.m_value=[]
      for l_url in l_m:
        a_fiddata.m_value.append(l_url)
        logging.debug('find one URL:%s',l_url)
    except Exception,e:
      raise Exception("URLReadRule("+self.m_pattern+")."+str(e))
    return True

class URL(FID):
  def __init__(self,a_url_pattern,a_writerule_code=None):
    super(URL,self).__init__('URLs',URLReadRule(a_url_pattern),WriteRule(a_writerule_code))

class HTML2HTML2CSV:
  def __init__(self, a_filename):
    self.m_filename=a_filename
    self.m_h2c=HTML2CSV(a_filename)
    self.m_url_list=[]
    self.m_urlfid_list=[]
    self.m_urldata_list=[]
    self.m_debug=None

  def debug_mode(self,a_bool):
    self.m_debug=a_bool
    self.m_h2c.debug_mode(a_bool)

  def add_fid(self,a_name,a_readrule_pattern,a_writerule_code=None):
    self.m_h2c.add_fid(a_name,a_readrule_pattern,a_writerule_code)
    return self

  def add_url(self, a_url):
    self.m_url_list.append(a_url)
    return self

  def add_urlfid(self, a_url_pattern, a_write_code=None):
    self.m_urlfid_list.append(URL(a_url_pattern,a_write_code))
    return self

  def fetch_url(self):
    l_fcache=None
    if self.m_debug:
      logging.debug('in debug mode so use cache')
      l_fcache=FileCache(lambda a_url:urllib2.urlopen(a_url).read())
    for l_url in self.m_url_list:
      logging.debug('fetching %s',l_url)

      l_html=HTML(l_url,self.m_urlfid_list,l_fcache)
      l_html.fetch()
      l_html.parse()
      for l_fd in l_html.m_fiddata_list:
        l_fd.write(None)
        for l_url in l_fd.m_value:
          if l_url not in self.m_urldata_list:
            self.m_urldata_list.append(l_url)
          else:
            logging.debug('ignore duplicated: %s',l_url)

  def convert(self):
    self.fetch_url()
    for l_url in self.m_urldata_list:
      self.m_h2c.add_url(l_url)
    self.m_h2c.convert()

class HTML2HTML2CSV_UT(unittest.TestCase):
  def test1(self):
    l_filename=inspect.stack()[0][3]+".csv"
    l_h2h2c=HTML2HTML2CSV(l_filename)
    l_h2h2c.debug_mode(True)
    l_h2h2c.add_url('http://www.52zhongtou.com/ProjectsDiscover/Discover')
    l_h2h2c.add_urlfid('(/ProjectView/Detail/pid/\d+)',
        '''if 1:
              l_list=[]
              for l_url in I:
                l_list.append('http://www.52zhongtou.com'+l_url)
              I=l_list
        '''
      )
    l_h2h2c.add_fid(
      'prj_name',
      '<h3 .*? href="/ProjectView/Detail/pid/\d+">(.*?)</a>'
      ).add_fid(
      'name',
      '来自 <a href="/User/UserProfile/id/\d+">(.*?)</a>'
      ).add_fid(
        'number_of_support',
        '已有</i>(.*)<i>个支持者'
      ).add_fid(
        'money',
        '获得</i>(.*)<i>元支持'
        ).add_fid(
            'average',
            None,
            '''if FIELD['number_of_support'] !='0':
            I=int(FIELD['money'])/int(FIELD['number_of_support']) 
      '''
      )
    l_h2h2c.convert()
    self.failUnless(open(l_filename).read() == open(l_filename+".exp").read())

def main():
    unittest.main()

if __name__ == '__main__':
    main()
