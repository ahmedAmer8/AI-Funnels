from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import re
import os
from urllib.parse import quote_plus
import time
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(model_name="gemini-2.5-flash")

app = FastAPI(title="Product Comparison API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProductRequest(BaseModel):
    url: str

class QuestionRequest(BaseModel):
    product_data: dict
    question: str

class ComparisonRequest(BaseModel):
    product_data: dict

def get_headers():
    """Get headers to mimic a real browser"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }

def extract_amazon_product(soup, url):
    """Extract product information from Amazon"""
    try:
        title_selectors = [
            '#productTitle',
            '.product-title',
            'h1[data-automation-id="product-title"]'
        ]
        title = None
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text().strip()
                break
        
        price_selectors = [
            '.a-price-whole',
            '.a-price .a-offscreen',
            '[data-automation-id="product-price"]',
            '.price-current'
        ]
        price = None
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price = price_elem.get_text().strip()
                break
        
        rating_selectors = [
            '.a-icon-alt',
            '[data-hook="average-star-rating"]',
            '.rating-score'
        ]
        rating = None
        for selector in rating_selectors:
            rating_elem = soup.select_one(selector)
            if rating_elem:
                rating_text = rating_elem.get_text()
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating = rating_match.group(1)
                break
        
        desc_selectors = [
            '#feature-bullets ul',
            '.product-description',
            '.product-features'
        ]
        description = None
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                description = desc_elem.get_text().strip()
                break
        
        reviews = []
        review_elements = soup.select('[data-hook="review-body"] span, .review-text')
        for review_elem in review_elements[:5]:  
            review_text = review_elem.get_text().strip()
            if review_text and len(review_text) > 10:
                reviews.append(review_text)
        
        return {
            'title': title or 'Title not found',
            'price': price or 'Price not available',
            'rating': rating or 'Rating not available',
            'description': description or 'Description not available',
            'reviews': reviews,
            'url': url,
            'source': 'Amazon'
        }
    except Exception as e:
        return {'error': f'Error extracting Amazon product: {str(e)}'}

def extract_generic_product(soup, url):
    """Extract product information from any website"""
    try:
        title_selectors = [
            'h1',
            '.product-title',
            '.product-name',
            '[itemprop="name"]',
            'title'
        ]
        title = None
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem and title_elem.get_text().strip():
                title = title_elem.get_text().strip()
                break
        
        price_selectors = [
            '.price',
            '.product-price',
            '[itemprop="price"]',
            '.cost',
            '.amount'
        ]
        price = None
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text().strip()
                if re.search(r'\$|\€|\£|\₹', price_text):
                    price = price_text
                    break
        
        desc_selectors = [
            '.product-description',
            '.description',
            '[itemprop="description"]',
            '.product-details'
        ]
        description = None
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                description = desc_elem.get_text().strip()[:500]  # Limit to 500 chars
                break
        
        rating = None
        rating_elements = soup.find_all(text=re.compile(r'\d+\.?\d*\s*(?:stars?|rating|/5)'))
        if rating_elements:
            for rating_text in rating_elements:
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating = rating_match.group(1)
                    break
        
        return {
            'title': title or 'Product title not found',
            'price': price or 'Price not available',
            'rating': rating or 'Rating not available', 
            'description': description or 'Description not available',
            'reviews': [],
            'url': url,
            'source': 'Generic Store'
        }
    except Exception as e:
        return {'error': f'Error extracting product: {str(e)}'}

@app.post("/scrape-product")
async def scrape_product(request: ProductRequest):
    """Scrape product information from a given URL"""
    try:
        headers = get_headers()
        response = requests.get(request.url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        if 'amazon.' in request.url.lower():
            product_data = extract_amazon_product(soup, request.url)
        else:
            product_data = extract_generic_product(soup, request.url)
        
        return {"success": True, "data": product_data}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error scraping product: {str(e)}")

@app.post("/ask-question")
async def ask_question(request: QuestionRequest):
    """Ask AI-powered questions about the product"""
    try:
        product = request.product_data
        question = request.question
        
        context = f"""
        Product Information:
        Title: {product.get('title', 'N/A')}
        Price: {product.get('price', 'N/A')}
        Rating: {product.get('rating', 'N/A')}
        Description: {product.get('description', 'N/A')}
        Reviews: {' | '.join(product.get('reviews', [])[:3])}
        
        User Question: {question}
        
        Please provide a helpful and accurate answer based on the product information above.
        """
        
        response = model.generate_content(context)
        
        return {
            "success": True, 
            "answer": response.text
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing question: {str(e)}")

def detect_region_from_url(url: str):
    """Detect region/country from URL"""
    region_mapping = {
        'amazon.com': 'US',
        'amazon.co.uk': 'UK', 
        'amazon.de': 'DE',
        'amazon.fr': 'FR',
        'amazon.it': 'IT',
        'amazon.es': 'ES',
        'amazon.ca': 'CA',
        'amazon.com.au': 'AU',
        'amazon.in': 'IN',
        'amazon.com.br': 'BR',
        'amazon.com.mx': 'MX',
        'amazon.sa': 'SA',
        'amazon.ae': 'AE',
        'amazon.eg': 'EG',
        'amazon.com.tr': 'TR',
        'amazon.sg': 'SG',
        'amazon.co.jp': 'JP',
        
        'noon.com': 'AE',  
        'jumia.com.eg': 'EG', 
        'jumia.co.ke': 'KE', 
        'jumia.com.ng': 'NG',  
        'flipkart.com': 'IN', 
        'souq.com': 'AE',  
        'carrefour.com': 'FR',
        'walmart.com': 'US',
        'target.com': 'US',
        'bestbuy.com': 'US',
        'currys.co.uk': 'UK',
        'mediamarkt.de': 'DE',
        'fnac.com': 'FR',
        'rakuten.co.jp': 'JP',
        'taobao.com': 'CN',
        'tmall.com': 'CN'
    }
    
    for domain, region in region_mapping.items():
        if domain in url.lower():
            return region
    
    return 'US'

def get_regional_platforms(region: str, search_query: str):
    """Get platforms to search based on detected region"""
    
    regional_platforms = {
        'EG': [ 
            {
                'name': 'Amazon Egypt',
                'search_url': f'https://www.amazon.eg/s?k={quote_plus(search_query)}',
                'selectors': {
                    'products': '[data-component-type="s-search-result"]',
                    'title': 'h2 a span',
                    'price': '.a-price-whole, .a-price .a-offscreen',
                    'link': 'h2 a'
                }
            },
            {
                'name': 'Noon Egypt',
                'search_url': f'https://www.noon.com/egypt-en/search/?q={quote_plus(search_query)}',
                'selectors': {
                    'products': '.productContainer',
                    'title': '.productTitle',
                    'price': '.currency, .price',
                    'link': 'a'
                }
            },
            {
                'name': 'Jumia Egypt',
                'search_url': f'https://www.jumia.com.eg/catalog/?q={quote_plus(search_query)}',
                'selectors': {
                    'products': '.prd',
                    'title': '.name',
                    'price': '.prc',
                    'link': 'a'
                }
            }
        ],
        'AE': [ 
            {
                'name': 'Amazon UAE',
                'search_url': f'https://www.amazon.ae/s?k={quote_plus(search_query)}',
                'selectors': {
                    'products': '[data-component-type="s-search-result"]',
                    'title': 'h2 a span',
                    'price': '.a-price-whole, .a-price .a-offscreen',
                    'link': 'h2 a'
                }
            },
            {
                'name': 'Noon UAE',
                'search_url': f'https://www.noon.com/uae-en/search/?q={quote_plus(search_query)}',
                'selectors': {
                    'products': '.productContainer',
                    'title': '.productTitle',
                    'price': '.currency, .price',
                    'link': 'a'
                }
            }
        ],
        'SA': [ 
            {
                'name': 'Amazon Saudi',
                'search_url': f'https://www.amazon.sa/s?k={quote_plus(search_query)}',
                'selectors': {
                    'products': '[data-component-type="s-search-result"]',
                    'title': 'h2 a span',
                    'price': '.a-price-whole, .a-price .a-offscreen',
                    'link': 'h2 a'
                }
            },
            {
                'name': 'Noon Saudi',
                'search_url': f'https://www.noon.com/saudi-en/search/?q={quote_plus(search_query)}',
                'selectors': {
                    'products': '.productContainer',
                    'title': '.productTitle', 
                    'price': '.currency, .price',
                    'link': 'a'
                }
            }
        ],
        'IN': [
            {
                'name': 'Amazon India',
                'search_url': f'https://www.amazon.in/s?k={quote_plus(search_query)}',
                'selectors': {
                    'products': '[data-component-type="s-search-result"]',
                    'title': 'h2 a span',
                    'price': '.a-price-whole, .a-price .a-offscreen',
                    'link': 'h2 a'
                }
            },
            {
                'name': 'Flipkart',
                'search_url': f'https://www.flipkart.com/search?q={quote_plus(search_query)}',
                'selectors': {
                    'products': '._1AtVbE',
                    'title': '._4rR01T',
                    'price': '._30jeq3',
                    'link': 'a'
                }
            }
        ],
        'US': [  
            {
                'name': 'Amazon US',
                'search_url': f'https://www.amazon.com/s?k={quote_plus(search_query)}',
                'selectors': {
                    'products': '[data-component-type="s-search-result"]',
                    'title': 'h2 a span',
                    'price': '.a-price-whole, .a-price .a-offscreen',
                    'link': 'h2 a'
                }
            },
            {
                'name': 'eBay',
                'search_url': f'https://www.ebay.com/sch/i.html?_nkw={quote_plus(search_query)}',
                'selectors': {
                    'products': '.s-item',
                    'title': '.s-item__title',
                    'price': '.s-item__price',
                    'link': '.s-item__link'
                }
            },
            {
                'name': 'Walmart',
                'search_url': f'https://www.walmart.com/search/?query={quote_plus(search_query)}',
                'selectors': {
                    'products': '[data-automation-id="product-title"]',
                    'title': '[data-automation-id="product-title"]',
                    'price': '[itemprop="price"]',
                    'link': 'a'
                }
            }
        ],
        'UK': [  
            {
                'name': 'Amazon UK',
                'search_url': f'https://www.amazon.co.uk/s?k={quote_plus(search_query)}',
                'selectors': {
                    'products': '[data-component-type="s-search-result"]',
                    'title': 'h2 a span',
                    'price': '.a-price-whole, .a-price .a-offscreen',
                    'link': 'h2 a'
                }
            },
            {
                'name': 'eBay UK',
                'search_url': f'https://www.ebay.co.uk/sch/i.html?_nkw={quote_plus(search_query)}',
                'selectors': {
                    'products': '.s-item',
                    'title': '.s-item__title',
                    'price': '.s-item__price',
                    'link': '.s-item__link'
                }
            }
        ]
    }
    
    return regional_platforms.get(region, regional_platforms['US'])

def search_similar_products(product_title: str, original_url: str, max_results: int = 3):
    """Search for similar products on different platforms based on region"""
    similar_products = []
    
    search_query = re.sub(r'[^\w\s]', ' ', product_title).strip()
    search_query = ' '.join(search_query.split()[:5])  
    
    region = detect_region_from_url(original_url)
    
    platforms = get_regional_platforms(region, search_query)
    
    headers = get_headers()
    
    for platform in platforms:
        try:
            response = requests.get(platform['search_url'], headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                products = soup.select(platform['selectors']['products'])[:3]
                
                for product in products:
                    try:
                        title_elem = product.select_one(platform['selectors']['title'])
                        price_elem = product.select_one(platform['selectors']['price'])
                        link_elem = product.select_one(platform['selectors']['link'])
                        
                        if title_elem and link_elem:
                            title = title_elem.get_text().strip()
                            price = price_elem.get_text().strip() if price_elem else 'N/A'
                            link = link_elem.get('href', '')
                            
                            if link and not link.startswith('http'):
                                if platform['name'].startswith('Amazon'):
                                    if 'amazon.eg' in platform['search_url']:
                                        link = 'https://www.amazon.eg' + link
                                    elif 'amazon.ae' in platform['search_url']:
                                        link = 'https://www.amazon.ae' + link
                                    elif 'amazon.sa' in platform['search_url']:
                                        link = 'https://www.amazon.sa' + link
                                    elif 'amazon.in' in platform['search_url']:
                                        link = 'https://www.amazon.in' + link
                                    elif 'amazon.co.uk' in platform['search_url']:
                                        link = 'https://www.amazon.co.uk' + link
                                    else:
                                        link = 'https://www.amazon.com' + link
                                elif platform['name'] == 'eBay' or platform['name'] == 'eBay UK':
                                    if 'ebay.co.uk' in platform['search_url']:
                                        link = 'https://www.ebay.co.uk' + link
                                    else:
                                        link = 'https://www.ebay.com' + link
                                elif 'noon.com' in platform['search_url']:
                                    link = 'https://www.noon.com' + link
                                elif 'jumia.com' in platform['search_url']:
                                    link = 'https://www.jumia.com.eg' + link
                                elif 'flipkart.com' in platform['search_url']:
                                    link = 'https://www.flipkart.com' + link
                            
                            similar_products.append({
                                'title': title,
                                'price': price,
                                'url': link,
                                'platform': platform['name']
                            })
                    except:
                        continue
            
            time.sleep(1)  
        except:
            continue
    
    return similar_products

@app.post("/compare-products")
async def compare_products(request: ComparisonRequest):
    """Find and compare similar products from other websites"""
    try:
        original_product = request.product_data
        product_title = original_product.get('title', '')
        
        similar_products = search_similar_products(product_title, original_product.get('url', ''))
        
        if not similar_products:
            return {
                "success": True,
                "comparison": "No similar products found on other platforms.",
                "similar_products": []
            }
        
        comparison_context = f"""
        Original Product:
        Title: {original_product.get('title', 'N/A')}
        Price: {original_product.get('price', 'N/A')}
        Rating: {original_product.get('rating', 'N/A')}
        Source: {original_product.get('source', 'N/A')}
        Region: {detect_region_from_url(original_product.get('url', ''))}
        
        Similar Products Found in Same Region:
        """
        
        for i, product in enumerate(similar_products, 1):
            comparison_context += f"""
        {i}. {product['title']} - {product['price']} ({product['platform']})
        """
        
        comparison_context += """
        
        Please provide a detailed comparison analysis including:
        1. Price comparison in the same regional currency
        2. Which regional platforms have similar products
        3. Recommendations based on regional availability and pricing
        4. Any notable differences or similarities
        5. Best value for money in this region
        """
        
        response = model.generate_content(comparison_context)
        
        return {
            "success": True,
            "comparison": response.text,
            "similar_products": similar_products
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error comparing products: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Product Comparison API is running!"}