import re
import time
import random
import requests
import pandas as pd
import requests.exceptions
from proxy import get_proxies
from collections import deque
from bs4 import BeautifulSoup
from urllib.parse import urlsplit
from urllib.parse import urlparse

def delay() -> None:
    time.sleep(random.uniform(15, 30))
    return None

def write_new_proxies():
    try:
        proxies = get_proxies()
        f=open('proxy_list.txt','w')
        for proxy in proxies:
            f.write(proxy+'\n')
        f.close()
        print ("DONE")
    except:
        print ("MAJOR ERROR")

def url_extraction(starting_url):
    parsed_uri = urlparse(starting_url)
    result = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    # print("extracted url: ", result)
    return result

def read_proxy_file():
    proxy_file = "proxy_list.txt"
    f = open(proxy_file, 'r')
    proxies = f.readlines()
    converted_proxies = []
    for element in proxies:
        converted_proxies.append(element.strip())
    return converted_proxies

if __name__ == '__main__':
    # starting url.
    starting_url = 'https://www.sfu.ca/economics/faculty/active-faculty.html'

    # a queue of urls to be crawled
    unprocessed_urls = deque([starting_url])

    # set of already crawled urls for email
    processed_urls = set()

    # a set of fetched emails
    emails = set()
    parts1 = urlsplit(starting_url)
    user_entered_netloc = parts1.netloc
    print(user_entered_netloc)
    #main_url_name = url_extraction(user_entered_netloc)
    p = re.compile(r"([^\.]*)\.([^\.]*)$")
    result = p.search(user_entered_netloc)
    base_mail_name = result.group(0)
    base_mail_name = re.sub("\.", "\\.", base_mail_name)

    email_regex = r"[a-z0-9\.\-+_]+@" + base_mail_name
    print("base mail Name: ", base_mail_name)
    print("email_regex: ", email_regex)


    print("user_entered_netloc: ", user_entered_netloc)
    file_name = 'email_dataset/sfu_emails.csv'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    write_new_proxies()
    proxies_list = read_proxy_file()
    index = 0
    #print(proxies_list)
    proxy = {"http": "http://" + proxies_list[index]}

    count_flag = 1

    # process urls one by one from unprocessed_url queue until queue is empty
    while len(unprocessed_urls):

        # move next url from the queue to the set of processed urls
        url = unprocessed_urls.popleft()
        processed_urls.add(url)

        # extract base url to resolve relative links
        parts = urlsplit(url)
        base_url = "{0.scheme}://{0.netloc}".format(parts)
        # print("base_url: ", base_url)

        path = url[:url.rfind('/') + 1] if '/' in parts.path else url

        # print("path: ", path)

        # Every 10 requests, generate a new proxy
        if count_flag % 10 == 0:
            index = index + 1
            proxy = {"http": "http://" + proxies_list[index]}

        delay()

        # get url's content
        print("Crawling URL %s" % url, " using proxy: ", proxy)

        try:
            # make request to the given url
            response = requests.get(url, headers=headers, proxies=proxy)

            # increment the count_flag
            count_flag = count_flag + 1
        except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
            # ignore pages with errors and continue with next url
            del proxies_list[index]
            print('Proxy ' + proxies_list[index] + ' deleted.')
            index = index + 1
            proxy = {"http": "http://" + proxies_list[index]}
            continue

        # set the pandas Dataframe
        df = pd.DataFrame(columns=['url', 'mail'])

        # extract all email addresses and add them into the resulting set
        # You may edit the regular expression as per your requirement
        new_emails = set(re.findall(email_regex, response.text, re.I))
        print("new_emails", new_emails)

        # read the main emails dataset file
        file_df = pd.read_csv(file_name)
        # make like of mails which already exists in file
        mail_list = file_df['mail'].to_list()

        # check if the email set is not empty
        if len(new_emails) != 0:
            for mail in new_emails:
                if len(mail_list) == 0:
                    df.loc[df.shape[0]] = [str(url), mail]
                else:
                    if mail not in mail_list:
                        # append the url and mail to dataframe
                        df.loc[df.shape[0]] = [str(url), mail]

            # Pass if dataframe is empty
            if df.empty:
                pass
            else:
                # Append dataframe to csv file
                df.to_csv(file_name, sep=',', header=None, mode='a', index=False)

        emails.update(new_emails)
        print("emails: ", emails)
        # create a beutiful soup for the html document
        soup = BeautifulSoup(response.text, 'lxml')

        # Once this document is parsed and processed, now find and process all the anchors i.e. linked urls in this document
        for anchor in soup.find_all("a"):
            # extract link url from the anchor
            link = anchor.attrs["href"] if "href" in anchor.attrs else ''
            # resolve relative links (starting with /)
            if link.startswith('/'):
                link = base_url + link
            elif not link.startswith('http'):
                link = path + link
            # add the new url to the queue if it was not in unprocessed list nor in processed list yet
            if not link in unprocessed_urls and not link in processed_urls:
                parts2 = urlsplit(link)
                base_url_netloc = parts2.netloc
                # Enter the links in the queue if the based netloc matched the entered url
                if base_url_netloc == user_entered_netloc:
                    unprocessed_urls.append(link)
