# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
#from scrapy.spiders import CrawlSpider, Rule

# 1. 导入RedisCrawlSpider类，不使用CrawlSpider
from scrapy_redis.spiders import RedisCrawlSpider
from scrapy.spiders import Rule

from dytt_redis_slaver.items import DyttRedisSlaverItem
import re
from selenium import webdriver
#import time

# class DyttSlaverSpider(CrawlSpider):
# 2. 修改父类 RedisCrawlSpider
class DyttSlaverSpider(RedisCrawlSpider):
    name = 'dytt_slaver'

    # 3. 取消 allowed_domains() 和 start_urls
    # allowed_domains = ['dy2018.com']
    # start_urls = ['https://www.dy2018.com/2/index.html']

    # 4. 增加redis-key
    redis_key = 'dytt:start_urls'

    # page_links = LinkExtractor(allow=r'/index_\d*.html')
    movie_links = LinkExtractor(allow=r'/i/\d*.html', restrict_xpaths=('//div[@class="co_content8"]'))

    rules = (
        # Rule(page_links),
        Rule(movie_links, callback='parse_item'),
    )

    # # 5. 增加__init__()方法，动态获取allowed_domains()
    # def __init__(self, *args, **kwargs):
    #     domain = kwargs.pop('domain', '')
    #     self.allowed_domains = filter(None, domain.split(','))
    #     super(DyttSlaverSpider, self).__init__(*args, **kwargs)

    def parse_item(self, response):
        # for Zoom in response.xpath('//div[@id="Zoom"]'):
        #     # Xpath会有偏差 改用正则表达式
        #     items = DyttRedisSlaverItem()
        #     # 译名
        #     items['name'] = Zoom.xpath('//p[2]/text()').extract()[0]
        #     # 年代
        #     items['year'] = Zoom.xpath('//p[4]/text()').extract()[0]
        #     # 产地
        #     items['origin'] = Zoom.xpath('//p[5]/text()').extract()[0]
        #     # 语言
        #     items['language'] = Zoom.xpath('//p[7]/text()').extract()[0]
        #     # 上映日期
        #     items['release_date'] = Zoom.xpath('//p[9]/text()').extract()[0]
        #     # 豆瓣评分
        #     items['douban_score'] = Zoom.xpath('//p[10]/text()').extract()[0]
        #     # 文件大小
        #     items['file_size'] = Zoom.xpath('//p[14]/text()').extract()[0]
        #     # 片长
        #     items['film_time'] = Zoom.xpath('//p[15]/text()').extract()[0]
        #     # 简介
        #     items['introduction'] = Zoom.xpath('//p[2]/text()').extract()[0]
        #     # 海报
        #     items['posters'] = re.search(r'◎简　　介</p>([\s\S]*)<p>◎影片截图', str(response.body, encoding="gbk")).group(1)
        #     # 下载链接(js加载，直接抓取不到，需要用selenium)
        #     items['download_link'] = Zoom.xpath("//a//@*[9]").extract()
        items = DyttRedisSlaverItem()

        str_resp = response.body.decode('gb2312', errors='ignore')
        rep_chars = ['&nbsp;', '&middot;', '&ldquo;', '&rdquo;', '&hellip;']
        for rep in rep_chars:
            str_resp = str_resp.replace(rep, '')

        title = re.search(r'◎片　　名(.*?)</.+>', str_resp).group(1).replace(u'\u3000', '')
        translation = re.search(r'◎译　　名(.*?)</.+>', str_resp).group(1).replace(u'\u3000', '')
        # 名字
        items['name'] = title + "|" + translation
        # 年代
        items['year'] = re.search(r'◎年　　代(.*?)</.+>', str_resp).group(1).replace(u'\u3000', '')
        # 评分
        try:
            items['score'] = response.xpath("//strong[@class='rank']/text()").extract()[0].replace(u'\u3000', '')
        except:
            items['score'] = '无评分'
            # 语言
        items['language'] = re.search(r'◎语　　言(.*?)</.+>', str_resp).group(1).replace(u'\u3000', '')
        # 上映日期
        items['release_date'] = re.search(r'◎上映日期(.*?)</.+>', str_resp).group(1).replace(u'\u3000', '')
        # 文件大小
        items['file_size'] = re.search(r'◎文件大小(.*?)</.+>', str_resp).group(1).replace(u'\u3000', '')
        # 片长
        items['film_time'] = re.search(r'◎片　　长(.*?)</.+>', str_resp).group(1).replace(u'\u3000', '')
        # 简介
        items['introduction'] = re.search(r'◎简　　介</.+>\r\n<.+>(.*?)</.+>', str_resp).group(1).replace(u'\u3000', '')
        # 海报
        items['posters'] = response.xpath("//div[@id='Zoom']/*[1]/img/@src").extract()[0]
        # 下载链接
        items['download_link'] = self.get_download_link(response.url)

        print(items)
        yield items

    def get_download_link(self, url):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(chrome_options=chrome_options)
        driver.get(url)
        #time.sleep(1)
        link = re.search(r'\"(thunder:.*?)\"',  driver.page_source).group(1)
        driver.close()
        return link

