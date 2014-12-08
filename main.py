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

class parsed_request():
    method = "NONE"
    full_url = ""
    uri = ""
    args_line = ""
    args = dict()

    def __init__(self, method, uri):
        self.method = method
        self.full_url = uri
        self.parse_uri(uri)
        self.parse_args()

    def parse_uri(self, uri):
        uri_separator_position = uri.find("?")
        if uri_separator_position >= 0:
            self.uri = uri[:uri_separator_position]
            self.args_line = uri[uri_separator_position+1:]
        else:
            self.uri = uri

    def get_full_url(self):
        return self.full_url

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

    def __init__(self):
        browser = os.environ.get('TTHA2BROWSER', 'CHROME')

        self.driver = Remote(
            command_executor='http://127.0.0.1:4444/wd/hub',
            desired_capabilities=getattr(DesiredCapabilities, browser).copy()
        )
        self.driver.maximize_window()

    def visit_page(self, target):
        print target
        self.driver.get(target)
        results = self.wait_and_find_many("a[href]")

        for i in results:
            link = i.get_attribute("href")
            if not (link in self.links):
                self.links[link] = False

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
        results =  WebDriverWait(self.driver, 30, 0.1).until(
           lambda d: d.find_elements_by_css_selector(targetName)
        )
        # print ("found " + str(len(results)))
        return results
        


if __name__ == '__main__':
    if len(sys.argv) != 2:
        #call("ls", shell=True)
        print "incorrect options, input only one option: target"
    else:

        file_path = "/tmp/xss_scaner_tcp.dump"

        pid = 0
        try:
            pid = os.fork()
        except OSError as exc:
            raise Exception("%s [%d]" % (exc.strerror, exc.errno))

        if pid == 0:
            # TODO set buffer max size to not save uselsess data
            call(["sudo tcpdump -i wlan0 -n -v -s 0 -A 'tcp and dst host " + sys.argv[1] + " and dst port 80' > " + file_path], shell=True)
        
        scaner = selenium_scaner()
        scaner.scan_site_with_selenium("http://" + sys.argv[1])
        os.kill(pid, signal.SIGTERM)


        requests = parse_file(file_path)
        print requests


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