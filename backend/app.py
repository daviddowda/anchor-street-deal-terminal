from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re
from datetime import datetime
app = Flask(__name__)
CORS(app)
DATA_FILE = os.path.join(os.path.dirname(__file__), 'pipeline.json')
SE_STATES = ['NC', 'SC', 'GA', 'FL', 'TN', 'North Carolina', 'South Carolina', 'Georgia', 'Florida', 'Tennessee']
SE_STATE_CODES = ['NC', 'SC', 'GA', 'FL', 'TN']
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}
def load_pipeline():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"deals": [], "next_id": 1}
def save_pipeline(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)
def parse_price(price_str):
    if not price_str:
        return None
    clean = re.sub(r'[^\d.]', '', price_str.replace(',', ''))
    try:
        return float(clean)
    except:
        return None
def scrape_bizbuysell():
    listings = []
    state_map = {
        'NC': 'north-carolina', 'SC': 'south-carolina',
        'GA': 'georgia', 'FL': 'florida', 'TN': 'tennessee'
    }
    for code, state_slug in state_map.items():
        try:
            url = f'https://www.bizbuysell.com/businesses-for-sale/{state_slug}/'
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, 'html.parser')
            cards = soup.select('div.listing-card, article.listing, div[data-testid="listing-card"]')
            if not cards:
                cards = soup.select('div.listing')
            for card in cards[:8]:
                title_el = card.select_one('h2 a, h3 a, .title a, a.listing-title')
                price_el = card.select_one('.asking-price, .price, [class*="price"]')
                revenue_el = card.select_one('.revenue, .gross-revenue, [class*="revenue"]')
                desc_el = card.select_one('.description, .summary, p')
                location_el = card.select_one('.location, .city-state, [class*="location"]')
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                href = title_el.get('href', '')
                link = href if href.startswith('http') else f'https://www.bizbuysell.com{href}'
                listings.append({
                    'id': f'bbs-{code}-{len(listings)}',
                    'source': 'BizBuySell',
                    'title': title,
                    'location': location_el.get_text(strip=True) if location_el else code,
                    'state': code,
                    'asking_price': parse_price(price_el.get_text() if price_el else ''),
                    'asking_price_raw': price_el.get_text(strip=True) if price_el else 'N/A',
                    'revenue_raw': revenue_el.get_text(strip=True) if revenue_el else 'N/A',
                    'description': desc_el.get_text(strip=True)[:200] if desc_el else '',
                    'url': link,
                    'scraped_at': datetime.now().isoformat(),
                    'status': 'new'
                })
            time.sleep(0.5)
        except Exception as e:
            print(f'BizBuySell {code} error: {e}')
    return listings
def scrape_bizquest():
    listings = []
    state_ids = {'NC': '34', 'SC': '40', 'GA': '11', 'FL': '10', 'TN': '43'}
    state_names = {'34': 'NC', '40': 'SC', '11': 'GA', '10': 'FL', '43': 'TN'}
    for code, sid in state_ids.items():
        try:
            url = f'https://www.bizquest.com/businesses-for-sale/?stateid={sid}'
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, 'html.parser')
            cards = soup.select('div.srp-listing, div.listing-item, article')
            for card in cards[:8]:
                title_el = card.select_one('h2 a, h3 a, a.listing-title, .biz-title a')
                price_el = card.select_one('.asking-price, .price-value, [class*="price"]')
                desc_el = card.select_one('.description, .listing-description, p')
                location_el = card.select_one('.location, .city-state, .listing-location')
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                href = title_el.get('href', '')
                link = href if href.startswith('http') else f'https://www.bizquest.com{href}'
                listings.append({
                    'id': f'bq-{code}-{len(listings)}',
                    'source': 'BizQuest',
                    'title': title,
                    'location': location_el.get_text(strip=True) if location_el else code,
                    'state': code,
                    'asking_price': parse_price(price_el.get_text() if price_el else ''),
                    'asking_price_raw': price_el.get_text(strip=True) if price_el else 'N/A',
                    'revenue_raw': 'N/A',
                    'description': desc_el.get_text(strip=True)[:200] if desc_el else '',
                    'url': link,
                    'scraped_at': datetime.now().isoformat(),
                    'status': 'new'
                })
            time.sleep(0.5)
        except Exception as e:
            print(f'BizQuest {code} error: {e}')
    return listings
def scrape_businessbroker():
    listings = []
    state_slugs = {
        'NC': 'north-carolina', 'SC': 'south-carolina',
        'GA': 'georgia', 'FL': 'florida', 'TN': 'tennessee'
    }
    for code, slug in state_slugs.items():
        try:
            url = f'https://www.businessbroker.net/listings/{slug}/'
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, 'html.parser')
            cards = soup.select('div.listing-item, div.srp-item, article.listing')
            for card in cards[:8]:
                title_el = card.select_one('h2 a, h3 a, a.listing-name, .listing-title a')
                price_el = card.select_one('.asking-price, .price, [class*="ask"]')
                revenue_el = card.select_one('.revenue, .gross-revenue, [class*="revenue"]')
                desc_el = card.select_one('.description, .listing-desc, p')
                location_el = card.select_one('.location, .listing-location, .city')
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                href = title_el.get('href', '')
                link = href if href.startswith('http') else f'https://www.businessbroker.net{href}'
                listings.append({
                    'id': f'bb-{code}-{len(listings)}',
                    'source': 'BusinessBroker.net',
                    'title': title,
                    'location': location_el.get_text(strip=True) if location_el else code,
                    'state': code,
                    'asking_price': parse_price(price_el.get_text() if price_el else ''),
                    'asking_price_raw': price_el.get_text(strip=True) if price_el else 'N/A',
                    'revenue_raw': revenue_el.get_text(strip=True) if revenue_el else 'N/A',
                    'description': desc_el.get_text(strip=True)[:200] if desc_el else '',
                    'url': link,
                    'scraped_at': datetime.now().isoformat(),
                    'status': 'new'
                })
            time.sleep(0.5)
        except Exception as e:
            print(f'BusinessBroker {code} error: {e}')
    return listings
def get_sample_listings():
    """Return realistic sample data when scraping doesn't yield results"""
    return [
        {
            'id': 'sample-1',
            'source': 'BizBuySell',
            'title': 'Established HVAC Company - Charlotte Metro',
            'location': 'Charlotte, NC',
            'state': 'NC',
            'asking_price': 1850000,
            'asking_price_raw': '$1,850,000',
            'revenue_raw': '$3.2M',
            'description': 'Well-established HVAC service and installation business with 15 years in operation. Strong recurring maintenance contracts. Owner retiring.',
            'url': 'https://www.bizbuysell.com',
            'scraped_at': datetime.now().isoformat(),
            'status': 'new'
        },
        {
            'id': 'sample-2',
            'source': 'BizQuest',
            'title': 'Commercial Cleaning & Janitorial Services',
            'location': 'Raleigh, NC',
            'state': 'NC',
            'asking_price': 675000,
            'asking_price_raw': '$675,000',
            'revenue_raw': '$1.1M',
            'description': 'B2B commercial cleaning company with long-term contracts. 22 employees. Owner operated. SBA eligible.',
            'url': 'https://www.bizquest.com',
            'scraped_at': datetime.now().isoformat(),
            'status': 'new'
        },
        {
            'id': 'sample-3',
            'source': 'BusinessBroker.net',
            'title': 'Plumbing & Drain Service Company',
            'location': 'Atlanta, GA',
            'state': 'GA',
            'asking_price': 2100000,
            'asking_price_raw': '$2,100,000',
            'revenue_raw': '$4.8M',
            'description': 'Residential and light commercial plumbing services. Established 2001. Fleet of 12 vehicles. Strong online reputation.',
            'url': 'https://www.businessbroker.net',
            'scraped_at': datetime.now().isoformat(),
            'status': 'new'
        },
        {
            'id': 'sample-4',
            'source': 'BizBuySell',
            'title': 'Landscaping & Lawn Care Business',
            'location': 'Nashville, TN',
            'state': 'TN',
            'asking_price': 890000,
            'asking_price_raw': '$890,000',
            'revenue_raw': '$1.9M',
            'description': 'Full-service commercial landscaping company. 85% recurring commercial accounts. 18 employees. Owner retiring after 20 years.',
            'url': 'https://www.bizbuysell.com',
            'scraped_at': datetime.now().isoformat(),
            'status': 'new'
        },
        {
            'id': 'sample-5',
            'source': 'BizQuest',
            'title': 'Auto Body & Collision Repair Shop',
            'location': 'Charleston, SC',
            'state': 'SC',
            'asking_price': 1250000,
            'asking_price_raw': '$1,250,000',
            'revenue_raw': '$2.4M',
            'description': 'DRP-approved collision center with 26 years of history. 8 bays, 14 employees. Real estate available separately.',
            'url': 'https://www.bizquest.com',
            'scraped_at': datetime.now().isoformat(),
            'status': 'new'
        },
        {
            'id': 'sample-6',
            'source': 'BizBuySell',
            'title': 'Electrical Contracting Company',
            'location': 'Tampa, FL',
            'state': 'FL',
            'asking_price': 3200000,
            'asking_price_raw': '$3,200,000',
            'revenue_raw': '$6.1M',
            'description': 'Commercial and residential electrical contractor. Licensed in FL. 28 employees including master electricians. Backlog of $2.1M.',
            'url': 'https://www.bizbuysell.com',
            'scraped_at': datetime.now().isoformat(),
            'status': 'new'
        },
        {
            'id': 'sample-7',
            'source': 'BusinessBroker.net',
            'title': 'Industrial Equipment Distributor',
            'location': 'Greensboro, NC',
            'state': 'NC',
            'asking_price': 4500000,
            'asking_price_raw': '$4,500,000',
            'revenue_raw': '$8.3M',
            'description': 'Regional distributor of industrial and safety equipment. 40-year operating history. Exclusive territory agreements with 3 major brands.',
            'url': 'https://www.businessbroker.net',
            'scraped_at': datetime.now().isoformat(),
            'status': 'new'
        },
        {
            'id': 'sample-8',
            'source': 'BizBuySell',
            'title': 'Pest Control Route Business',
            'location': 'Savannah, GA',
            'state': 'GA',
            'asking_price': 420000,
            'asking_price_raw': '$420,000',
            'revenue_raw': '$580K',
            'description': 'Established pest control route with 340 residential accounts. High recurring revenue. Owner will train.',
            'url': 'https://www.bizbuysell.com',
            'scraped_at': datetime.now().isoformat(),
            'status': 'new'
        },
    ]
@app.route('/api/scrape', methods=['GET'])
def scrape():
    try:
        all_listings = []
        all_listings.extend(scrape_bizbuysell())
        all_listings.extend(scrape_bizquest())
        all_listings.extend(scrape_businessbroker())

        # Filter: only SE states
        filtered = [l for l in all_listings if l.get('state') in SE_STATE_CODES]

        # If scraping yields nothing (blocked), return sample data
        if len(filtered) == 0:
            filtered = get_sample_listings()
            return jsonify({
                'listings': filtered,
                'count': len(filtered),
                'note': 'Live scraping was blocked by sites. Showing representative sample listings. Use the links to visit each source directly.',
                'scraped_at': datetime.now().isoformat()
            })

        return jsonify({
            'listings': filtered,
            'count': len(filtered),
            'scraped_at': datetime.now().isoformat()
        })
    except Exception as e:
        sample = get_sample_listings()
        return jsonify({
            'listings': sample,
            'count': len(sample),
            'note': f'Scraping error: {str(e)}. Showing sample listings.',
            'scraped_at': datetime.now().isoformat()
        })
@app.route('/api/pipeline', methods=['GET'])
def get_pipeline():
    data = load_pipeline()
    return jsonify(data['deals'])
@app.route('/api/pipeline', methods=['POST'])
def add_deal():
    data = load_pipeline()
    deal = request.json
    deal['id'] = f'deal-{data["next_id"]}'
    deal['created_at'] = datetime.now().isoformat()
    deal['updated_at'] = datetime.now().isoformat()
    if 'stage' not in deal:
        deal['stage'] = 'New Lead'
    data['deals'].append(deal)
    data['next_id'] += 1
    save_pipeline(data)
    return jsonify(deal), 201
@app.route('/api/pipeline/<deal_id>', methods=['PUT'])
def update_deal(deal_id):
    data = load_pipeline()
    for i, deal in enumerate(data['deals']):
        if deal['id'] == deal_id:
            data['deals'][i].update(request.json)
            data['deals'][i]['updated_at'] = datetime.now().isoformat()
            save_pipeline(data)
            return jsonify(data['deals'][i])
    return jsonify({'error': 'Not found'}), 404
@app.route('/api/pipeline/<deal_id>', methods=['DELETE'])
def delete_deal(deal_id):
    data = load_pipeline()
    data['deals'] = [d for d in data['deals'] if d['id'] != deal_id]
    save_pipeline(data)
    return jsonify({'success': True})
@app.route('/api/sources', methods=['GET'])
def get_sources():
    sources = [
        {'name': 'BizBuySell', 'url': 'https://www.bizbuysell.com', 'type': 'marketplace', 'scrapable': True, 'notes': 'Largest US marketplace'},
        {'name': 'BizQuest', 'url': 'https://www.bizquest.com', 'type': 'marketplace', 'scrapable': True, 'notes': 'Strong SE coverage'},
        {'name': 'BusinessBroker.net', 'url': 'https://www.businessbroker.net', 'type': 'marketplace', 'scrapable': True, 'notes': '30k+ listings'},
        {'name': 'Axial', 'url': 'https://www.axial.net', 'type': 'platform', 'scrapable': False, 'notes': 'Login required — lower middle market'},
        {'name': 'Sunbelt Network', 'url': 'https://www.sunbeltnetwork.com', 'type': 'broker-network', 'scrapable': False, 'notes': 'Manual outreach recommended'},
        {'name': 'MidStreet (NC)', 'url': 'https://www.midstreet.com', 'type': 'broker', 'scrapable': False, 'notes': 'HQ in NC — strong local fit'},
        {'name': 'Viking Mergers (SE)', 'url': 'https://www.vikingmergers.com', 'type': 'broker', 'scrapable': False, 'notes': '600+ businesses sold in SE'},
        {'name': 'ENLIGN (NC/SE)', 'url': 'https://enlign.com', 'type': 'broker', 'scrapable': False, 'notes': '$1M+ revenue focus'},
        {'name': 'Empire Flippers', 'url': 'https://empireflippers.com', 'type': 'marketplace', 'scrapable': False, 'notes': 'Online businesses — curated'},
        {'name': 'Sunbelt Atlanta', 'url': 'https://www.sunbeltatlanta.com', 'type': 'broker', 'scrapable': False, 'notes': 'GA focus'},
        {'name': 'DealStream', 'url': 'https://dealstream.com', 'type': 'marketplace', 'scrapable': False, 'notes': '20k+ listings'},
        {'name': 'WNC Business Brokerage', 'url': 'https://wncbusinessbrokerage.com', 'type': 'broker', 'scrapable': False, 'notes': 'Asheville/western NC'},
        {'name': 'BizBen', 'url': 'https://www.bizben.com', 'type': 'marketplace', 'scrapable': False, 'notes': 'Community + listings'},
        {'name': 'Generational Group', 'url': 'https://www.generational.com', 'type': 'broker', 'scrapable': False, 'notes': 'Middle market IB'},
        {'name': 'Facebook Groups', 'url': 'https://www.facebook.com/groups/smallbusinessforsale', 'type': 'social', 'scrapable': False, 'notes': '700k+ members — manual only'},
    ]
    return jsonify(sources)
if __name__ == '__main__':
    app.run(debug=True, port=5050)
