from selenium import webdriver
from bs4 import BeautifulSoup
from pprint import pprint
import time, re
import requests
import io, json

try:
    to_unicode = unicode
except NameError:
    to_unicode = str

API_KEY = '884e2067aa114ae5b25f8876dcaa051b'
MOST_VIEWED_URL = 'https://api.nytimes.com/svc/mostpopular/v2/mostviewed/all-sections/30.json?api-key=' + API_KEY
MOST_SHARED_URL = 'https://api.nytimes.com/svc/mostpopular/v2/mostshared/all-sections/30.json?api-key=' + API_KEY
MOST_EMAILED_URL = 'https://api.nytimes.com/svc/mostpopular/v2/mostemailed/all-sections/30.json?api-key=' + API_KEY

articles = {}
articles['data'] = {}

def get_date_in_url(url):
    index = url.find('/2017/')
    date = url[index:index + 12]
    return date.replace('/', '')

def is_valid_url(url):
    tests = []
    test1 = (url.find('/video/') == -1)
    tests.append(test1)
    test2 = (url.find('query.nytimes.com') == -1)
    tests.append(test2)
    test3 = (url.find('/2017/0') != -1)
    tests.append(test3)
    return test1 and test2 and test3

def get_article_metadata(month, day, year, type):
    archive_url = 'https://api.nytimes.com/svc/archive/v1/' + str(year) + '/' + str(month) + '.json?api-key=' + API_KEY
    archive_request = requests.get(archive_url)
    archive_data = archive_request.json()
    archive_docs = archive_data['response']['docs']
    # for i in range(0, 5000):
    for i in range(0, len(archive_docs)):
        url_done = False
        urlRetryCount = 1
        while (not url_done and urlRetryCount <= 10):
            try:
                doc = archive_docs[i]
                url = doc['web_url']
                if is_valid_url(url):
                    date = get_date_in_url(url)
                    if ((type == 'after' and int(date) >= int(str(year) + '0' + str(month) + str(day)) and int(date) <= int(str(year) + '0' + str(month) + str(31))) or
                        (type == 'before' and int(date) <= int(str(year) + '0' + str(month) + str(day)) and int(date) >= int(str(year) + '0' + str(month) + '01'))):
                        # print url
                        abridged_url = url[url.find('/2017'):]
                        if abridged_url not in articles['data']:
                            articles['data'][abridged_url] = doc
                            print 'Done scraping ' + url
                url_done = True
            except KeyError:
                print 'Failed scraping ' + url + ' Retry ' + str(urlRetryCount)
                url_done = False
                urlRetryCount += 1
                time.sleep(.05)
                continue
    return

def get_all_article_metadata(startMonth, startDay, endMonth, endDay, year):
    print 'Scraping article urls...'
    get_article_metadata(startMonth, startDay, year, 'after')
    if startMonth != endMonth:
        get_article_metadata(endMonth, endDay, year, 'before')
    print 'Done scraping article urls. '
    print str(len(articles['data'])) + ' article metadatas scraped.'

    with io.open('articles_final.json', 'w', encoding='utf-8') as outputFile:
    	str_ = json.dumps(articles,
                          indent=4, sort_keys=True,
                          separators=(',', ':'), ensure_ascii=False)
    	outputFile.write(to_unicode(str_))

def get_popularity_data(request_url, category):
    print 'Scraping ' + category

    done = False
    offset = 0
    while not done:
        popularity_request = requests.get(request_url + '&offset=' + str(offset))
        print request_url + '&offset=' + str(offset)
        popularity_data = popularity_request.json()
        popularity_results = popularity_data['results']

        for i in range(0, len(popularity_results)):
            url = popularity_results[i]['url']
            # print url
            if url[url.find('/2017'):] != -1:
                url = url[url.find('/2017'):]
            if url in articles['data']:
                articles['data'][url][category] = True
        offset += 20
        if (offset > popularity_data['num_results']):
            done = True

    for url in articles['data']:
        if category not in articles['data'][url]:
            articles['data'][url][category] = False
    print 'Done scraping ' + category

    with io.open('articles_final.json', 'w', encoding='utf-8') as outputFile:
    	str_ = json.dumps(articles,
                          indent=4, sort_keys=True,
                          separators=(',', ':'), ensure_ascii=False)
    	outputFile.write(to_unicode(str_))

def scrape_article_text(driver, url):
    text = ''
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    # print soup
    resultSoup = soup.find_all('p', class_='story-content')
    for element in resultSoup:
        text += element.get_text() + ' '
    return text

def scrape_all_articles():
    print 'Scraping article texts...'
    # driver = webdriver.PhantomJS()
    driver = webdriver.Edge()
    count = 1
    for url in articles['data']:
        web_url = articles['data'][url]['web_url']
        if count <= 20:
            article_done = False
            articleRetryCount = 1
            while (not article_done and articleRetryCount <= 10):
                try:
                    if 'text' not in articles['data'][url]:
                        print 'Scraping article ' + str(count) + ': ' + web_url
                        articles['data'][url]['text'] = scrape_article_text(driver, web_url)
                        count += 1
                    article_done = True
                except:
                    print 'Failed scraping article ' + str(count) + '. Retry ' + str(articleRetryCount) + ': ' + url
                    articleRetryCount += 1
                    time.sleep(2)
                    continue
            if count % 50 == 0:
                with io.open('articles_with_texts_final.json', 'w', encoding='utf-8') as outputFile:
                	str_ = json.dumps(articles,
                                      indent=4, sort_keys=True,
                                      separators=(',', ':'), ensure_ascii=False)
                	outputFile.write(to_unicode(str_))
    driver.close()

    with io.open('articles_with_texts_final.json', 'w', encoding='utf-8') as outputFile:
    	str_ = json.dumps(articles,
                          indent=4, sort_keys=True,
                          separators=(',', ':'), ensure_ascii=False)
    	outputFile.write(to_unicode(str_))

    print 'Done scraping article texts.'
    return

# Main Program

# get_all_article_metadata(3, 13, 4, 11, 2017)
with open('articles_with_texts_final.json') as data_file:
    articles = json.load(data_file)

# url = 'https://www.nytimes.com/2017/04/01/opinion/sunday/manhood-in-the-age-of-trump.html'
# # driver = webdriver.PhantomJS()
# driver = webdriver.Edge()
# text = scrape_article_text(driver, url)
# with io.open('example.txt', 'w', encoding='utf-8') as outputFile:
#     str_ = json.dumps(text,
#                       indent=4, sort_keys=True,
#                       separators=(',', ':'), ensure_ascii=False)
#     outputFile.write(to_unicode(str_))
# driver.close()

# get_popularity_data(MOST_VIEWED_URL, 'most_viewed')
# get_popularity_data(MOST_SHARED_URL, 'most_shared')
# get_popularity_data(MOST_EMAILED_URL, 'most_emailed')
# print len(articles['data'])
start = time.time()
print start
scrape_all_articles()
end = time.time()
print end
print str((end - start)/60) + ' minutes'

# count = 0
# for url in articles['data']:
#     if 'text' not in articles['data'][url]:
#         print articles['data'][url]['web_url']
#         count += 1
# print count
