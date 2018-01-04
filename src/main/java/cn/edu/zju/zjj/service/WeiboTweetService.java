package cn.edu.zju.zjj.service;

import cn.edu.zju.zjj.dao.WeiboTweetDao;
import cn.edu.zju.zjj.entity.WeiboTweet;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/**
 * author: zjj
 * <p>
 * Data: 2017/12/9 18:57
 */
@Service
public class WeiboTweetService extends  BaseService<WeiboTweet>{



    @Autowired
    private WeiboTweetService(WeiboTweetDao tweetDao){
        super(tweetDao);
    }
}
