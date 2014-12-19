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



LOG_ERROR = 1
LOG_XSS = 2
LOG_WARNING = 3
LOG_PROGRESS = 4
LOG_LOG = 5

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
            file_logger().trace("Most likely XSS found.\n"+
                        "Xss script was found in page\n"+
                        "Outputing page source code to file", LOG_XSS)
            file_logger().print_to_file(self.current_page + "\n" + self.driver.page_source + "\n\n")
            # print self.driver.page_source
            break
        if not problems_found:
            if self.driver.page_source.find(XSS_BLOCK) >= 0:
                file_logger().trace("Potential XSS found.\n"+
                            "Xss script was found in page\n"+
                            "Outputing page source code to file", LOG_XSS)
                file_logger().print_to_file(self.current_page + "\n" + self.driver.page_source + "\n\n")

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
        found_new_page = False
        file_logger().trace("visit " + target, LOG_PROGRESS)
        self.current_page = target
        self.driver.get(target)
        results = self.wait_and_find_many("a[href]")

        for i in results:
            link = i.get_attribute("href")
            if not (link in self.links):
                found_new_page = True
                self.links[link] = False

        self.check_page()

        self.links[target] = True
        return found_new_page


    def scan_site_with_selenium(self, target):
        self.target = target
        self.visit_page(target)

        not_all_links_checked = True
        while not_all_links_checked:
            not_all_links_checked = False
            for i in self.links:
                if self.links[i] == False:
                    not_all_links_checked = True
                    if self.visit_page(i):
                        break



        self.driver.quit()
        # sleep(5)


    def wait_and_find_many(self, targetName):
        # print ("looking for " + targetName)
        # results = self.driver.find_elements_by_css_selector(targetName)
        try:
            results =  WebDriverWait(self.driver, 0.1, 0.1).until(
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
                url = "http://" + self.target + uri

                file_logger().trace("checking " + url, LOG_PROGRESS)

                try:
                    response = urllib2.urlopen(url)
                    html = response.read()
                except Exception as exc:
                    file_logger().trace("Unable to get page: " + url, LOG_WARNING)
                    html = ""
                # print html
                if html.find(XSS_BLOCK) >= 0:

                    file_logger().trace("Potential XSS found.\n"+
                                "Xss script was found in page\n"+
                                "Outputing page source code to file", LOG_XSS)

                    file_logger().print_to_file(url + "\n" + html + "\n\n")
                    # print html

                k += 1
            # self.check_xss(html)
            # cur_target.get_uri


    # def check_xss(self, text_to_check):
    #     new_line = "1"
    #     while new_line:
    #         new_line = text_to_check.readline()
    #         if new_line.find(XSS_BLOCK):
    #             print "XSS FOUND"

def get_url(target):
    protocol_string = "http://"
    protocol_position = target.find(protocol_string)
    url = target
    if protocol_position >= 0:
        url = target[protocol_position+len(protocol_string):]

    return url
def get_host(target):
    url = get_url(target)

    host = url
    separator_position = url.find("/")
    if separator_position >= 0:
        host = url[:separator_position]
    return host

def get_ip(target):
    host = get_host(target)
    try:
        result = socket.gethostbyname(host)
    except Exception as exc:
        file_logger().trace("Failed to resolve address", LOG_ERROR)
        sys.exit()
    return result;


class file_logger():
    file_descriptor = None
    verbosity_level = 0

    def print_to_file(self, text):
        file_logger().trace(text, LOG_LOG)
        file_logger.file_descriptor.write(text)

    def open_file(self, file_name):
        file_logger.file_descriptor = open(file_name, 'w')

    def close_file(self):
        file_logger.file_descriptor.close()

    def trace(self, text, verbosity_level = 5):
        if file_logger.verbosity_level >= verbosity_level:
            if verbosity_level == 1:
                print "____------====ERROR====------____"
            elif verbosity_level == 2:
                print "____------=====XSS=====------____"
            elif verbosity_level == 3:
                print "____------===WARNING===------____"
            elif verbosity_level == 4:
                print "____------===PROGRESS===-----____"
            elif verbosity_level == 5:
                print "____------=====LOG=====------____"
            print text

    def set_verbosity_level(self, verbosity_level):
        temp_verbosity_level = 3;
        parse_ok = True
        try:
            temp_verbosity_level = int(verbosity_level)
            if temp_verbosity_level > 5 or temp_verbosity_level < 0:
                temp_verbosity_level = 3
                parse_ok = False
        except Exception as exc:
            parse_ok = False

        file_logger.verbosity_level = temp_verbosity_level

        if not parse_ok:
            file_logger().trace("Wrong verbosity level\n"+
                        "Possible values:\n"+
                        "0, nothing\n"+
                        "1, errors\n"+
                        "2, xss\n"+
                        "3, warnings\n"+
                        "4, progress\n"+
                        "5, file output", LOG_WARNING)

        file_logger().trace("Verbosity level set to " + str(file_logger.verbosity_level), LOG_WARNING)



if __name__ == '__main__':
    # file_logger().trace("-----------", 10)
    # 0 - nothing
    # 1 - errors
    # 2 - xss
    # 3 - warnings
    # 4 - progress
    # 5 - everything
    if len(sys.argv) < 3:
        file_logger().set_verbosity_level(LOG_ERROR)
        file_logger().trace("Incorrect options amount\n"+
                                "Required options:\n"+
                                "1. Target url\n"+
                                "2. Output file name/path\n"+
                                "Possible options:\n"+
                                "3. Verbosity level [0-5]", LOG_ERROR)
        sys.exit()

    target_url = get_url(sys.argv[1])
    target_host = get_host(sys.argv[1])
    target_ip = get_ip(sys.argv[1])

    dump_file_path = "xss_scaner_tcp.dump"
    output_file_path = sys.argv[2]
    file_logger().open_file(output_file_path)
    if len(sys.argv) == 4:
        file_logger().set_verbosity_level(sys.argv[3])
    else:
        file_logger().set_verbosity_level(3)

    file_logger().trace(
    "____------=============------____\n"+
    "____------== Phase 1 ==------____\n"+
    "____------=============------____", LOG_PROGRESS)
    pid = 0
    try:
        pid = os.fork()
    except OSError as exc:
        raise Exception("%s [%d]" % (exc.strerror, exc.errno))

    if pid == 0:
        # TODO set buffer max size to not save uselsess data
        call(["tcpdump -i wlan0 -n -v -s 0 -A 'tcp and dst host " + target_ip + " and dst port 80' > " + dump_file_path], shell=True)
    
    scaner = selenium_scaner()
    scaner.scan_site_with_selenium("http://" + target_url)
    os.kill(pid, signal.SIGTERM)


    file_logger().trace(
    "____------=============------____\n"+
    "____------== Phase 2 ==------____\n"+
    "____------=============------____", LOG_PROGRESS)

    requests = parse_file(dump_file_path)
    post_checker = wget_post_checker(target_host)
    post_checker.check_dict(requests)
    file_logger().close_file()

    pass