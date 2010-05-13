#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright 2009 N23 <wenjin.zhang@gmail.com>
# All rights reserved.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__all__ = ['get_smtp_client', 'sendmail']

import os, sys
from ConfigParser import ConfigParser
from ConfigParser import NoOptionError

from smtplib import SMTP
from smtplib import SMTPAuthenticationError
from email import Encoders
from email.base64MIME import encode as encode_base64
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

def get_smtp_client(stor):
    host = stor['host']
    port = stor['port']
    user = stor['user']
    passwd = stor['pass']
    debuglevel = stor['debuglevel']
    login = stor['login']
    starttls = stor['starttls']

    s = SMTP(host, port)
    if debuglevel:
        s.set_debuglevel(True)

    if starttls and login:
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(user, passwd)
    elif login:
        try:
            s.login(user, passwd)
        except SMTPAuthenticationError:
            sys.stdout.write('\n------- try Auth Login again ------\n')
            s = SMTP(host, port)
            if debuglevel:
                s.set_debuglevel(True)

            s.ehlo()
            (code, resp) = s.docmd('AUTH LOGIN')
            if code != 334:
                raise SMTPAuthenticationError(code, resp)
            (code, resp) = s.docmd(encode_base64(user, eol=""))
            if code != 334:
                raise SMTPAuthenticationError(code, resp)
            (code, resp) = s.docmd(encode_base64(passwd, eol=""))
            if code != 235:
                raise SMTPAuthenticationError(code, resp)

    return s    

def sendmail(server, msg):
    address = [i for f in ('To', 'Cc', 'Bcc') if msg[f] for i in msg[f].split(',')]
    server.sendmail(msg['From'], address, msg.as_string())

def fn(options, args):
    cfg = ConfigParser()
    cfg.read('LoginAccount.txt')

    flag = 'mailClient'
    keys = ('host', 'port', 'user', 'pass', 'fr', 'to', 'debuglevel', 'login', 'starttls')
    stor = {}
    for k in keys: stor.setdefault(k, '')

    try:
        stor['host'] = cfg.get(flag, 'host')
        stor['port'] = cfg.getint(flag, 'port')
        stor['user'] = cfg.get(flag, 'user')
        stor['pass'] = cfg.get(flag, 'pass')
        stor['fr'] = cfg.get(flag, 'fr')
        stor['to'] = cfg.get(flag, 'to')
        stor['debuglevel'] = cfg.getboolean(flag, 'debuglevel')
        stor['login'] = cfg.getboolean(flag, 'login')
        stor['starttls'] = cfg.getboolean(flag, 'starttls')
    except NoOptionError: pass

    if options.addr:
        stor['to'] = options.addr
   
    s = get_smtp_client(stor)
    for arg in args:
        sys.stdout.write('sending... ' + arg)
        msg = MIMEMultipart()
        msg['From'] = stor['fr']
        msg['Subject'] = arg
        msg['To'] = stor['to']
        msg.set_boundary('===== Baby, python is good =====')

        if not options.atta:
            data = MIMEBase('application', 'octet-stream')
            data.set_payload(open(arg, 'rb').read())
            Encoders.encode_base64(data)
            data.add_header('Content-Disposition', 'attachment', filename = arg)
            msg.attach(data)
        else:
            b = '''<html><head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
</head><body><pre>'''
            b += open(arg, 'rb').read()
            b += '''</pre></body></html>'''

            body = MIMEText(b, _subtype = 'html', _charset = 'utf-8')
            msg.attach(body)
        sendmail(s, msg)
        sys.stdout.write(' done.\n')
    s.close()

if __name__ == '__main__':

    from optparse import OptionParser
    usage = '%prog [-e addr] [-a] args...'
    parser = OptionParser(usage=usage)
    parser.add_option('-e', '--addr', dest='addr',
                      help='receive email address', metavar='address')
    parser.add_option('-a', '--atta', dest='atta',
                      action='store_true', default=False,
                      help='attachment flag')
    (options, args) = parser.parse_args()
    print args
    if not args:
        parser.print_usage()
        sys.exit(1)

    fn(options, args)

