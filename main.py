#!/usr/bin/env python2

import os
import sys
import httplib, urllib
import base64
import sys
import signal
from subprocess import call
from time import sleep

from selenium.webdriver import ActionChains, DesiredCapabilities, Remote
from selenium.webdriver.support.ui import WebDriverWait

import urllib2

import socket


XSS_SELECTOR = "script[id='xss']"
XSS_BLOCK = "<script id='xss'> </script>"
XSS_URL_BLOCK = "%3cscript+id%3d%27xss%27%3e+%3c%2fscript%3e"

"""

<html><body bgcolor='#cccccc'><title>XSS FUN!!</title><center><img src = 'dog.jpg'>
<br><br>Hello <script id='xss'> </script>. whatchu wanna do now?<br></html>

"""

class parsed_request():
    # method = "NONE"
    # full_url = ""
    # uri = ""
    # args_line = ""

    def __init__(self, method, uri):
        self.method = method
        self.full_url = uri
        self.args = dict()

        self.parse_uri(uri)
        self.parse_args()
        #print self.args

    def parse_uri(self, uri):
        #print uri
        uri_separator_position = uri.find("?")
        self.args_line = ""
        if uri_separator_position >= 0:
            self.uri = uri[:uri_separator_position]
            self.args_line = uri[uri_separator_position+1:]
        else:
            self.uri = uri

    def get_full_url(self):
        return self.full_url

    def get_uri(self):
        return self.uri

    def get_args(self):
        return self.args

    def parse_args(self):
        if not self.args_line:
            return
        parse_line = self.args_line
        while parse_line:
            parse_line_separator_position = parse_line.find("&")

            if parse_line_separator_position >= 0:
                args_pair = parse_line[:parse_line_separator_position]
                parse_line = parse_line[parse_line_separator_position+1:]
            else:
                args_pair = parse_line
                parse_line = ""


            args_pair_separator_position = args_pair.find("=")

            args_first = args_pair[:args_pair_separator_position]
            args_second = args_pair[args_pair_separator_position+1:]

            self.args[args_first] = args_second




    def get_uri_without_args(self):
        pass


    def __repr__(self):
        # print self.args
        return self.method + " " + self.uri + " " + self.args_line + " " + str(self.args)
    def __str__(self):
        # print self.args
        return self.method + " " + self.uri + " " + self.args_line + " " + str(self.args)


def parse_file(file_name):
    # print "parse_file"
    # print file_name
    opened_file = open(file_name)
    requests = dict()
    new_request = get_request_from_file(opened_file)
    while new_request:

        full_url = new_request.get_full_url()
        requests[full_url] = new_request
        new_request = get_request_from_file(opened_file)

    return requests


def get_request_from_file(opened_file):
    # print "get_request_from_file"
    # print opened_file
    request_line = find_request(opened_file)
    if not request_line:
        return None
    request = parse_line(request_line)
    return request


def find_request(opened_file):
    # print "find_request"
    # print opened_file
    http_tag_position = -1
    current_line = ""
    while http_tag_position < 0:
        current_line = opened_file.readline()
        if not current_line:
            break
        http_tag_position = current_line.find("HTTP/1.1")
    return current_line

def parse_line(line):
    # print "find_request"
    # print line
    request_method = "NONE"
    request_method_position = -1;
    if line.find("GET") >= 0:
        request_method_position = line.find("GET")
        request_method = "GET"
    elif line.find("POST") >= 0:
        equest_method_position = line.find("POST")
        request_method = "POST"
    else:
        request_method = "UNDIFINED"
        return None

    request_line = line[request_method_position:]
    # print "request_line " + "'" + request_line + "'"

    request_uri_start_position = request_line.find(" ");
    # print "request_uri_start_position", request_uri_start_position

    request_line_from_uri = request_line[(request_uri_start_position+1):]

    request_uri_end_position = request_line_from_uri.find(" ");
    # print "request_line_from_uri" + "'" + request_line_from_uri + "'"
    # print "request_uri_end_position", request_uri_end_position

    return parsed_request(request_method, request_line_from_uri[:request_uri_end_position])


# class link():
#     visited = False
#     uri = ""

#     def __init__(self, uri):
#         self.uri = uri
#         self.visited = False

class selenium_scaner():
    links = dict()

    current_page = ""
    current_submit_button = 0
    current_submit_input = 0

    def __init__(self):
        browser = os.environ.get('TTHA2BROWSER', 'CHROME')

        self.driver = Remote(
            command_executor='http://127.0.0.1:4444/wd/hub',
            desired_capabilities=getattr(DesiredCapabilities, browser).copy()
        )
        self.driver.maximize_window()

    def check_xss(self):
        problems_found = False
        problems = self.wait_and_find_many(XSS_SELECTOR)
        for i in problems:
            problems_found = True
            print "____------===WARNING===------____"
            print "------high chance XSS found------"
            print "---xss script was found in DOM---"
            print "---outputing page source code----"
            print self.driver.page_source
            break
        if not problems_found:
            if self.driver.page_source.find(XSS_BLOCK) >= 0:
                print "____------===WARNING===------____"
                print "------high chance XSS found------"
                print "---xss script was found in page---"
                print "---outputing page source code----"
                print self.driver.page_source
        pass


    def check_page(self):
        self.current_submit_button = -1
        self.current_submit_input = -1

        inputs_checked = False
        submits_checked = False

        while ((not inputs_checked) or (not submits_checked)):
            text_input_fields = self.wait_and_find_many('input[type="text"]')
            password_input_fields = self.wait_and_find_many('input[type="password"]')
            text_areas = self.wait_and_find_many('textarea')
            submit_inputs = self.wait_and_find_many('input[type="submit"]')
            submit_buttons = self.wait_and_find_many('button[type="submit"]')

            for i in text_input_fields:
                i.send_keys(XSS_BLOCK)

            for i in password_input_fields:
                i.send_keys(XSS_BLOCK)

            for i in text_areas:
                i.send_keys(XSS_BLOCK)

            inputs_checked = True
            for i in submit_inputs:
                if i > self.current_submit_input:
                    self.current_submit_input = i
                    inputs_checked = False
                    i.click()

            if inputs_checked == True:
                submits_checked = True
                for i in submit_buttons:
                    if i >= self.current_submit_button:
                        self.current_submit_button = i
                        submits_checked = False
                        i.click()

            self.check_xss()
            self.driver.get(self.current_page)



    def visit_page(self, target):
        print "visit " + target
        self.current_page = target
        self.driver.get(target)
        results = self.wait_and_find_many("a[href]")

        for i in results:
            link = i.get_attribute("href")
            if not (link in self.links):
                self.links[link] = False

        self.check_page()

        self.links[target] = True


    def scan_site_with_selenium(self, target):
        self.target = target
        self.visit_page(target)

        not_all_links_checked = True
        while not_all_links_checked:
            not_all_links_checked = False
            for i in self.links:
                if self.links[i] == False:
                    not_all_links_checked = True
                    self.visit_page(i)


        self.driver.quit()
        # sleep(5)


    def wait_and_find_many(self, targetName):
        # print ("looking for " + targetName)

        try:
            results =  WebDriverWait(self.driver, 1, 0.2).until(
               lambda d: d.find_elements_by_css_selector(targetName)
            )
        except Exception as exc:
            results = []
        # print ("found " + str(len(results)))
        return results

class wget_post_checker():
    target = ""

    def __init__(self, target):
        self.target = target
        # browser = os.environ.get('TTHA2BROWSER', 'CHROME')

        # self.driver = Remote(
        #     command_executor='http://127.0.0.1:4444/wd/hub',
        #     desired_capabilities=getattr(DesiredCapabilities, browser).copy()
        # )
        # self.driver.maximize_window()

    def check_dict(self, targets_dict):
        for i in targets_dict:

            cur_target = targets_dict[i]
            args = cur_target.get_args()


            k = 0
            while k < len(args):
                uri = cur_target.get_uri()
                if len(args) > 0:
                    uri += "?"

                j = 0
                for i in args:
                    uri += i
                    uri += "="
                    if k == j:
                        uri += XSS_URL_BLOCK
                    else:
                        uri += args[i]
                    if j < len(args):
                        uri += "&"
                    j += 1

                print "checking " + "http://" + self.target + uri
                try:
                    response = urllib2.urlopen("http://" + self.target + uri)
                    html = response.read()
                except Exception as exc:
                    html = ""
                print html
                if html.find(XSS_BLOCK) >= 0:
                    print "____------===WARNING===------____"
                    print "------high chance XSS found------"
                    print "---xss script was found in page---"
                    print "---outputing page source code----"
                    print html

                k += 1
            # self.check_xss(html)
            # cur_target.get_uri


    # def check_xss(self, text_to_check):
    #     new_line = "1"
    #     while new_line:
    #         new_line = text_to_check.readline()
    #         if new_line.find(XSS_BLOCK):
    #             print "XSS FOUND"

def getHost(target):
    # /print "target: " + target
    separator_position = target.find("/")
    host = target

    if separator_position > 0:
        host = target[:separator_position]
        # print "cutted"
    return host

def getIp(target):
    # /print "target: " + target
    separator_position = target.find("/")
    host = target

    if separator_position > 0:
        host = target[:separator_position]
        # print "cutted"

    # print "result host:" + host
    result = socket.gethostbyname(host)
    return result;
    # print "ip: " + result


if __name__ == '__main__':

    # print zlib.compress('echo "hell" | nc 10.20.2.253 8182')
    # print zlib.decompress("4f9d09eb344f6")


    if len(sys.argv) != 2:
        #call("ls", shell=True)
        print "incorrect options, input only one option: target ip"
    else:
        target_host = getHost(sys.argv[1])
        target_ip = getIp(target_host)

        file_path = "/tmp/xss_scaner_tcp.dump"

        print "----------------=================================----------------"
        print "-------------================== Phase 1 ============-------------"
        print "----------------=================================----------------"
        pid = 0
        try:
            pid = os.fork()
        except OSError as exc:
            raise Exception("%s [%d]" % (exc.strerror, exc.errno))

        if pid == 0:
            # TODO set buffer max size to not save uselsess data
            call(["sudo tcpdump -i wlan0 -n -v -s 0 -A 'tcp and dst host " + target_ip + " and dst port 80' > " + file_path], shell=True)
        
        scaner = selenium_scaner()
        scaner.scan_site_with_selenium("http://" + sys.argv[1])
        os.kill(pid, signal.SIGTERM)


        print "----------------=================================----------------"
        print "-------------================== Phase 2 ============-------------"
        print "----------------=================================----------------"
        requests = parse_file(file_path)
        # post_checker = wget_post_checker("http://" + sys.argv[1])
        post_checker = wget_post_checker(target_host)
        post_checker.check_dict(requests)

        # print requests


    # requests = parse_file("/home/trizalio/test.dump")
    # print len(sys.argv)
    # print sys.argv
    # files = os.listdir(".")
    # print files
    # dump_file = open("/home/trizalio/test.dump")

    # current_request_type = "NONE"

    # current_line = find_request(dump_file)

    # http_tag_position = -1
    # current_line = ""
    # while http_tag_position < 0:
    #     current_line = dump_file.readline()
    #     if not current_line:
    #         break
    #     http_tag_position = current_line.find("HTTP/1.1")

    # if current_line.find("GET") >= 0:
    #     current_request_type = "GET"
    # elif current_line.find("POST") >= 0:
    #     current_request_type = "POST"
    # else:
    #     current_request_type = "UNDIFINED"

    # print current_line
    # print current_request_type

    # while current_line:

    # for line in dump_file:
    #     print line

    # print dump_file.readline()

    # commandCoded = base64.b64encode(sys.argv[1])
    # params = urllib.urlencode({'stalk': commandCoded})
    # headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    # conn = httplib.HTTPConnection("10.20.2.181")
    # conn.request("POST", "/?mod=inc/mgrz&asp=mypass", params, headers)
    # response = conn.getresponse()
    # print response.status, response.reason
    # data = response.read()
    # conn.close()

    pass