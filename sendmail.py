#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import sqlite3

class mailPool:
    def __init__(self, dbpath):
        self.table_name = 'email_pool'
        self.dbpath = dbpath
        self.conn = sqlite3.connect(self.dbpath)
        self.conn.isolation_level = None
        sql = "create table if not exists " + self.table_name + " (\
            `id` integer primary key autoincrement, \
            `from` varchar(255), \
            `to` varchar(255), \
            `status` interger,\
            `send_time` interger, \
            `subject` varchar(255), \
            `content` text \
            )";
        self.conn.execute(sql)
        self.conn.commit()
    
    def add(self, content):
        head = self.parseHeader(content)

        if not (head.has_key('subject') and head.has_key('to')):
            raise Exception('no subject or to')
        tpl_sql = "insert into %s (`status`, `subject`, `to`, `content`) values (0, ?, ?, ?)"
        sql = tpl_sql % (self.table_name, )
        cur = self.conn.cursor()
        cur.execute(sql, (head['subject'],  head['to'], content))
        ecmail_id =  cur.lastrowid
    
    def getCount(self):
        sql = "select count(*) from " + self.table_name + " where status = 0"
        cur = self.conn.cursor()
        cur.execute(sql)

        return cur.fetchone()[0]

    def getOne(self):
        sql = "select * from " + self.table_name + " where status = 0 order by id desc Limit 1"
        cur = self.conn.cursor()
        cur.execute(sql)

        return cur.fetchone()

    def setStart(self, mail_id):
        tpl_sql = "update %s set status = 1 where id = %d and status = 0"
        sql = tpl_sql % (self.table_name, mail_id)
        cur = self.conn.cursor()
        cur.execute(sql)
        return cur.rowcount
    
    def setEnd(self, mail_id):
        tpl_sql = "update %s set status = 2 where id = %d and status = 1"
        sql = tpl_sql % (self.table_name, mail_id)
        cur = self.conn.cursor()
        cur.execute(sql)
        return cur.rowcount
    
    def parseHeader(self, content):
        head = content[0:content.find("\n\n", 0, 200)]
        #tmp = head.split("\n")
        tmp = [line.split(':') for line in head.split("\n")]
        ret = {}
        for row in tmp:
            if len(row) > 1 :
                ret[row[0].lower()] =  row[1]

        return ret

if __name__ == '__main__':
    from optparse import OptionParser
    usage = '%prog [-f sqlit db path] [-t test is ok]'
    parser = OptionParser(usage = usage)
    parser.add_option('-f', '--file', help="sqlit db path", metavar="FILE")
    parser.add_option('-t', '--test', action="store_true", default=False)
    (options, args) = parser.parse_args()
    if not options.file:
        parser.print_usage()
        sys.exit(-1)
    try:
        msg = sys.stdin.read()
        pool = mailPool(options.file)
        pool.add(msg)
    except Exception, data:
        import time
        f = open(options.file + '.log', 'a')
        f.write(time.strftime('%Y-%m-%d %H:%M:%S') + "\n" + str(data) + "\n")
        f.close()
        sys.exit(-1)
    