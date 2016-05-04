import json
import os

import requests
from bs4 import BeautifulSoup as BS


RESPONSES_DIR = './responses/'


class Detail(object):

    def __init__(self, fn):
        self.id = fn.replace('.html', '')
        self.name = None
        self.address = None
        self.district = None
        self.city = None
        self.state = None
        self.cep = None
        self.phones = None
        self.emails = None
        self.site = None
        self.contact_name = None
        self.export_price_range = None
        self.activity_sector = None
        self.countries = []
        self.products = []

        with open(os.path.join(RESPONSES_DIR, fn)) as fp:
            self.html = BS(fp, 'lxml')

        self.rows = self.html.find_all('tr')
        if self.rows:
            try:
                self.set_name()
                self.set_address()
                self.set_phones()
                self.set_emails()
                self.set_site()
                self.set_export_price_range()
                self.set_activity_sector()
                self.set_countries()
                self.set_products()
            except Exception as e:
                print(self.id)
                print(self.html.text)
                raise e

    def set_name(self):
        self.name = self.html.find('h3').text

    def set_address(self):
        raw = self.rows[1].text.split('Endereço ')[1].strip()
        self.address, self.district, place, cep = list(map(lambda x: x.strip(), raw.split(' | ')))
        self.cep = self.set_cep(cep)

        raw = place.split('-')
        self.city, self.state = raw if raw == 2 else '-'.join(raw[:-1]) ,raw[-1]

    def set_cep(self, cep):
        cep = cep.replace('CEP: ', '')
        if len(cep) != 8:
            cep = '0' + cep
        return '{}-{}'.format(cep[:5], cep[5:])

    def set_phones(self):
        numbers = self.rows[2].text.split(' | ')
        f = lambda x, y: {'type': x.lower(), 'number': y.strip()}
        g = lambda x: x.split(':', 1)
        self.phones = [f(*g(number)) for number in numbers]

    def set_emails(self):
        self.emails = self.rows[3].text.split()[1:]

    def set_site(self):
        raw = self.rows[4].text.split(u'\xa0\xa0\xa0')
        self.website = self.strip(raw[0]) if len(raw) >= 2 else None
        self.contact_name = self.strip(raw[1]) if len(raw) >= 2 else self.strip(raw[0])

    def set_export_price_range(self):
        raw = self.rows[5].text
        self.export_price_range = self.strip(raw)

    def set_activity_sector(self):
        raw = self.rows[6].text
        self.activity_sector = raw.replace('Setor de atividade: ', '')

    def set_countries(self):
        table = self.html.find_all('thead')[2]
        countries = [td.text for td in table.find_all('td')]
        self.countries = countries

    def set_products(self):
        table = self.html.find_all('thead')[4]
        f = lambda x, y: {'code': x, 'name': y}
        g = lambda x: tuple(x.text.split(' - ', 1))
        products = [f(*g(td)) for td in table.find_all('td')]
        self.products = products

    def strip(self, s):
        return s.split(': ')[-1]

    def __str__(self):
        s = """ID: {obj.id}
Name: {obj.name}
Address: {obj.address}
District: {obj.district}
City: {obj.city}
State: {obj.state}
Cep: {obj.cep}
Phones: {obj.phones}
Email: {obj.email}
Site: {obj.site}
Contact name: {obj.contact_name}
Export price range: {obj.export_price_range}
Activity sector: {obj.activity_sector}
Countries: {obj.countries}
Products: {obj.products}
"""
        return s.format(obj=self)

    def __json__(self):
        d = {
            'name': self.name,
            'address': self.address,
            'district': self.district,
            'city': self.city,
            'state': self.state,
            'cep': self.cep,
            'phones': self.phones,
            'emails': self.emails,
            'site': self.site,
            'contact_name': self.contact_name,
            'export_price_range': self.export_price_range,
            'activity': self.activity_sector,
            'countries': self.countries,
            'products': self.products,
        }
        return d

class Scraper(object):

    BASE_URL = 'http://www.brazil4export.com'
    LIST_URL = os.path.join(
        BASE_URL,
        'include_php/functions.php?opc=1&tabela=0&cpo_busca=&page='
    )
    DETAIL_URL = os.path.join(
        BASE_URL,
        'include_php/functions.php?opc=6&empresa='
    )
    RESPONSE_DIR = 'responses'

    def __init__(self):
        self.session = requests.Session()
        self.session.get(self.BASE_URL)
        self.ids = set()
        self.details = set()

    def load_ids(self, fn):
        with open(fn) as fp:
            self.ids = json.load(fp)

    def append_id(self, link):
        self.ids.add(link.attrs['onclick'][12:-1])

    def append_ids(self, links):
        for link in links:
            self.append_id(link)

    def append_links(self, html):
        links = BS(html).find_all(attrs={'href': '#pop_detail'})
        self.append_ids(links)

    def extract_id(self, id):
        url = self.LIST_URL + str(id)
        response = self.session.get(url)
        self.append_links(response.text)

    def extract_ids(self, n):
        for id in range(1, n+1):
            self.extract_id(id)

    def save_responses(self):
        for id in self.ids:
            self.save_response(id)

    def save_response(self, id):
        url = self.DETAIL_URL + str(id)
        response = self.session.get(url)
        with open(os.path.join(self.RESPONSE_DIR, '{}.html'.format(id)), 'w') as fp:
            fp.write(response.text)


if __name__ == '__main__':
    # scraper = Scraper()
    # scraper.extract_ids(821)
    # scraper.load_ids('ids.json')
    import os, json
    files = os.listdir('responses')
    companies = (Detail(fn) for fn in files)
    for company in companies:
        json.dump(company.__json__(), open(os.path.join('json', company.id + '.json'), 'w'))
