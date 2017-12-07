# encoding=utf-8
import re
import datetime
from scrapy.spiders import CrawlSpider
from scrapy.selector import Selector
from scrapy.http import Request
from WeiboSpider.items import InformationItem, TweetsItem, FollowsItem, FansItem, CommentItem, FlagItem
from WeiboSpider.constant import *
from WeiboSpider.settings import PROPERTIES
from bs4 import BeautifulSoup
import ssl
import json

ssl._create_default_https_context = ssl._create_unverified_context


class Spider(CrawlSpider):
    name = "WeiboSpider"
    host = "https://weibo.cn"
    start_urls = PROPERTIES['users']
    scrawl_id = set(start_urls)  # 记录待爬的微博ID
    finish_id = set()  # 记录已爬的微博ID
    comment_pattern = 'https://weibo.cn/comment/%s?page=%d'
    follow_pattern = "https://weibo.cn/%s/follow"
    like_pattern = "https://m.weibo.cn/api/container/getSecond?" \
                   "containerid=100505%s_-_WEIBO_SECOND_PROFILE_LIKE_WEIBO&page=%d"
    info_pattern = "https://weibo.cn/%s/info"

    def start_requests(self):
        while self.scrawl_id.__len__():
            ID = self.scrawl_id.pop()
            self.finish_id.add(ID)  # 加入已爬队列
            ID = str(ID)
            follows = []
            follows_items = FollowsItem()
            follows_items["_id"] = ID
            follows_items["follows"] = follows
            fans = []
            fansItems = FansItem()
            fansItems["_id"] = ID
            fansItems["fans"] = fans

            url_follows = self.follow_pattern % ID  # url_follows = "http://weibo.cn
            like_url = self.like_pattern % (ID, 1)
            url_fans = "http://weibo.cn/%s/fans" % ID
            url_tweets = "http://weibo.cn/%s?page=1" % ID
            url_information1 = "http://weibo.cn/%s/info" % ID
            url_information = "http://weibo.cn/attgroup/opening?uid=%s" % ID
            weibo_id = 'FniYTADUE'
            meta_data = {"id": ID, "current_page": 1}
            yield Request(url=url_follows, meta={"item": follows_items, "result": follows},
                          callback=self.parse_follow)  # 去爬关注人
            # yield Request(url=url_fans, meta={"item": fansItems, "result": fans}, callback=self.parse3)  # 去爬粉丝
            # yield Request(url=url_information1, meta={"ID": ID}, callback=self.parse_info)  # 去爬个人信息
            # yield Request(url=url_tweets, meta={"ID": ID, "current_page": 1}, callback=self.parse_weibo)  # 去爬微博
            # yield Request(url=like_url, meta=meta_data, callback=self.parse_weibo2)
            # yield Request(url=comment_url, meta={"weiboId": weibo_id}, callback=self.parse_comment)

    def parse_comment(self, response):

        weiboId = response.meta['weiboId']
        selector = Selector(response)
        comments = selector.xpath('body/div[@class="c" and starts-with(@id, "C_")]')
        current_page = response.meta['current_page']
        for c in comments:
            commentItem = CommentItem()
            commentItem['weibo_id'] = weiboId
            # print comments
            commentItem["user"] = c.xpath('a/text()').extract_first()
            user = c.xpath('span[@class="ctt"]/a/text()').extract_first()
            comments = c.xpath('span[@class="ctt"]/text()').extract()
            comments.insert(1, user if user else "")
            commentItem["content"] = ''.join(comments)

            others = c.xpath('span[@class="ct"]/text()').extract_first()
            if others:
                others = others.split(u"\u6765\u81ea")
                commentItem["time"] = others[0]
                if len(others) == 2:
                    commentItem["source"] = others[1]
            yield commentItem
        # print selector.xpath(u'body/div[@id="pagelist"]/form').extract_first()
        next_page_url = selector.xpath(u'body/div[@id="pagelist"]/form/div/a[text()="下页"]/@href').extract_first()
        next_page = current_page + 1
        if 'max_page' not in response.meta:
            # print selector.xpath('body/div[@id="pagelist"]')
            max_page = selector.xpath('body/div[@id="pagelist"]/form/div/input[@name="mp"]/@value').extract_first()
            if max_page:
                response.meta['max_page'] = int(max_page)
            else:
                flag_item = FlagItem()
                flag_item['weibo_id'] = weiboId
                yield flag_item
                return
        if next_page < response.meta['max_page']:
            response.meta['current_page'] = next_page
            # print "next page" + str(next_page)
            yield Request(url=self.comment_pattern % (weiboId, next_page), meta=response.meta,
                          callback=self.parse_comment)
        else:
            flag_item = FlagItem()
            flag_item['weibo_id'] = weiboId
            yield flag_item

    def parse0(self, response):
        """ 抓取个人信息1 """
        info = InformationItem()
        selector = Selector(response)
        text0 = selector.xpath('body/div[@class="u"]/div[@class="tip2"]').extract_first()
        if text0:
            num_tweets = re.findall(u'\u5fae\u535a\[(\d+)\]', text0)  # 微博数
            num_follows = re.findall(u'\u5173\u6ce8\[(\d+)\]', text0)  # 关注数
            num_fans = re.findall(u'\u7c89\u4e1d\[(\d+)\]', text0)  # 粉丝数
            if num_tweets:
                info["tweets_num"] = int(num_tweets[0])
            if num_follows:
                info["follows_num"] = int(num_follows[0])
            if num_fans:
                info["fans_num"] = int(num_fans[0])
            info["_id"] = response.meta["ID"]
            url_information1 = "http://weibo.cn/%s/info" % response.meta["ID"]
            yield Request(url=url_information1, meta={"item": info}, callback=self.parse_info)

    def parse_info(self, response):
        """ 抓取个人信息2 """
        info = InformationItem()
        selector = Selector(response)
        all_text = []
        base_info_index, edu_info_index, work_info_index = -1, -1, -1
        base_info = ''
        edu_info = ''
        work_info = ''
        tags = ''
        div_list = list(selector.xpath('body/div[@class="c" or @class="tip" ]'))
        for index, div in enumerate(div_list):
            text = div.xpath('text()').extract_first()
            if text == u'基本信息':
                base_info_index = index
            elif text == u'学习经历':
                edu_info_index = index
            elif text == u'工作经历':
                work_info_index = index
        if base_info_index != -1:
            b = BeautifulSoup(div_list[base_info_index+1].extract())
            tags = ','.join(map(lambda a: a.get_text(), b.find_all('a')))
            base_info = b.get_text(';')
        if edu_info_index != -1:
            b = BeautifulSoup(div_list[edu_info_index+1].extract())
            edu_info = b.get_text(';')

        if work_info_index != -1:
            b = BeautifulSoup(div_list[work_info_index+1].extract())
            work_info = b.get_text(';')

        text1 = ";".join(all_text)  # 获取标签里的所有text()
        nickname = re.findall(u'\u6635\u79f0[:|\uff1a](.*?);', base_info)  # 昵称
        gender = re.findall(u'\u6027\u522b[:|\uff1a](.*?);', base_info)  # 性别
        place = re.findall(u'\u5730\u533a[:|\uff1a](.*?);', base_info)  # 地区（包括省份和城市）
        signature = re.findall(u'\u7b80\u4ecb[:|\uff1a](.*?);', base_info)  # 个性签名
        birthday = re.findall(u'\u751f\u65e5[:|\uff1a](.*?);', base_info)  # 生日
        sex_orientation = re.findall(u'\u6027\u53d6\u5411[:|\uff1a](.*?);', base_info)  # 性取向
        marriage = re.findall(u'\u611f\u60c5\u72b6\u51b5[:|\uff1a](.*?);', base_info)  # 婚姻状况
        url = re.findall(u'\u4e92\u8054\u7f51[:|\uff1a](.*?);', text1)  # 首页链接
        info['tags'] = tags
        info["nick_name"] = nickname[0] if nickname else ''
        info["gender"] = gender[0] if gender else ''
        info["location"] = place[0] if place else ''
        info["signature"] = signature[0] if signature else ''
        if birthday:
            try:
                birthday = datetime.datetime.strptime(birthday[0], "%Y-%m-%d")
                info["birthday"] = birthday - datetime.timedelta(hours=8)
            except Exception:
                info["birthday"] = ''
                pass
        info['work_info'] = work_info
        info['edu_info'] = edu_info
        info["sex_orientation"] = sex_orientation[0] if sex_orientation else u'未知'
        info["marriage"] = marriage[0] if marriage else u'未知'
        info["url"] = url[0] if url else ''
        yield info

    def parse_weibo2(self, response):
        json_data = json.loads(response.text)
        if response.meta['current_page'] == 1:
            response.meta['max_page'] = int(json_data['count']) / 10
        response.meta['current_page'] += 1

        def map_func(card):
            print card['mblog']['text']
        if 'cards' in json_data:
            map(map_func, json_data['cards'])
        if response.meta['current_page'] <= response.meta['max_page']:
            yield Request(url=self.like_pattern % (response.meta['id'], response.meta['current_page']),
                          meta=response.meta, callback=self.parse_weibo2)
        pass

    def parse_weibo(self, response):
        """ 抓取微博数据 """
        selector = Selector(response)
        tweets = selector.xpath('body/div[@class="c" and @id]')
        for tweet in tweets:
            tweet_item = TweetsItem()
            weibo_id = tweet.xpath('@id').extract_first()[2:]  # 微博ID
            cmts = tweet.xpath('div/span[@class="cmt"]').extract()
            if len(tweet.xpath('div/span[@class="cmt"]').extract()) > 2:
                content = tweet.xpath(u'div/span[text() = "转发理由:"]/../text()').extract_first()
                tweet_item['Type'] = REPOST
                coordinates = None
            else:
                content = tweet.xpath('div/span[@class="ctt"]/text()').extract_first()  # 微博内容
                coordinates = tweet.xpath('div/a/@href').extract_first()  # 定位坐标
                tweet_item['Type'] = ORIGINAL
            like = re.findall(u'\u8d5e\[(\d+)\]', tweet.extract())  # 点赞数
            transfer = re.findall(u'\u8f6c\u53d1\[(\d+)\]', tweet.extract())  # 转载数
            comment = re.findall(u'\u8bc4\u8bba\[(\d+)\]', tweet.extract())  # 评论数
            others = tweet.xpath('div/span[@class="ct"]/text()').extract_first()  # 求时间和使用工具（手机或平台）

            tweet_item["ID"] = response.meta["ID"]
            comment_url = self.comment_pattern % (weibo_id, 1)

            tweet_item["_id"] = response.meta["ID"] + "-" + weibo_id
            if content:
                tweet_item["Content"] = content.strip(u"[\u4f4d\u7f6e]")  # 去掉最后的"[位置]"
            if coordinates:
                coordinates = re.findall('center=([\d|.|,]+)', coordinates)
                if coordinates:
                    tweet_item["Coordinates"] = coordinates[0]
            if like:
                tweet_item["Like"] = int(like[0])
            if transfer:
                tweet_item["Transfer"] = int(transfer[0])
            if comment:
                tweet_item["Comment"] = int(comment[0])
            if others:
                others = others.split(u"\u6765\u81ea")
                tweet_item["PubTime"] = others[0]
                if len(others) == 2:
                    tweet_item["Tools"] = others[1]

            yield Request(url=comment_url, meta={"weiboId": weibo_id, "current_page": 1}, callback=self.parse_comment)
            yield tweet_item
        next_page = response.meta['current_page'] + 1
        if 'max_page' not in response.meta:
            print selector.xpath('body/div[@id="pagelist"]')
            max_page = selector.xpath('body/div[@id="pagelist"]/form/div/input[@name="mp"]/@value').extract_first()
            if max_page:
                response.meta['max_page'] = int(max_page)
            else:
                return
        print response.meta['max_page']
        if next_page <= response.meta['max_page']:
            response.meta['current_page'] = next_page
            yield Request(url=self.host + '/' + response.meta['ID'] + '?page=' + str(next_page),
                          meta=response.meta, callback=self.parse_weibo)

    def parse_follow(self, response):
        """ 抓取关注或粉丝 """
        items = response.meta["item"]

        selector = Selector(response)
        # //table/ttbody/tr/td/a[text()="关注他" '
        # u'or text()="关注她"'
        #    u'or text()="取消关注"]/@href
        text2 = selector.xpath(
            u'//body/table/tr/td/a[text()="取消关注" or text()="关注她" or text()="关注他"]/@href').extract()
        print '\n'.join(text2)
        for elem in text2:
            elem = re.findall('uid=(\d+)', elem)
            if elem:
                response.meta["result"].append(elem[0])
                ID = int(elem[0])
                if ID not in self.finish_id:  # 新的ID，如果未爬则加入待爬队列
                    # self.scrawl_id.add(ID)
                    yield Request(url=self.info_pattern % ID, callback=self.parse_info)  # 去爬个人信息
                    # break
        url_next = selector.xpath(
            u'body//div[@class="pa" and @id="pagelist"]/form/div/a[text()="\u4e0b\u9875"]/@href').extract()
        if url_next:
            # pass
            yield Request(url=self.host + url_next[0], meta={"item": items, "result": response.meta["result"]},
                          callback=self.parse_follow)
        else:  # 如果没有下一页即获取完毕
            yield items
