# -*- coding: cp936 -*-

from ctypes import *
from setting import LOGGER

class YunDaMa:
    YDMApi = windll.LoadLibrary('.\\dll\\yundamaAPI-x64.dll')
    appId = 4296  # ����ɣģ������߷ֳɱ�Ҫ��������¼�����ߺ�̨���ҵ��������ã�
    appKey = b'fdacec8d9f1c2deb86346bfcf64e95f2'  # �����Կ�������߷ֳɱ�Ҫ��������¼�����ߺ�̨���ҵ��������ã�

    def __init__(self, username, password):
        LOGGER.info('app id��%d\r\napp key��%s' % (self.appId, self.appKey))
        self.username = b'zhujiajun'
        self.password = b'vs7452014'
        self.code_type = 1005
        self.timeout = 60
        self.YDMApi.YDM_SetAppInfo(self.appId, self.appKey)

    def recognize(self, filename):
        if not isinstance(filename, bytes):
            filename = filename.encode()
        result = c_char_p(b"                              ")
        LOGGER.info('\r\n>>>���ڵ�½...')
        captcha_id = self.YDMApi.YDM_EasyDecodeByPath(self.username, self.password, self.appId, self.appKey,
                                                      filename, self.code_type, self.timeout, result)

        return captcha_id, result.value

        # ��һ������ʼ���ƴ��룬ֻ�����һ�μ���


if __name__ == '__main__':
    i, code = YunDaMa(username='zhujiajun', password='vs7452014').recognize(
        'D:\\graduate\\WeiboSpider3\\img\\verify_code.png')
    print(type(code))
    print(bytes.decode(code))
    print(len(bytes.decode(code)))
    print(code)
