# AI Product Comparison Chatbot 🛍️

A comprehensive system that allows users to analyze products from any online store, ask AI-powered questions, and compare with similar products across multiple platforms.

## Features ✨

- **Universal Product Scraping**: Extract product info from Amazon, eBay, Walmart, and other online stores
- **AI-Powered Q&A**: Ask natural language questions about products using Gemini AI
- **Cross-Platform Comparison**: Automatically find and compare similar products from different websites
- **Interactive Streamlit Interface**: User-friendly chat interface for seamless interaction


## Quick Start 🚀

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Gemini AI API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Configure YOUR_GEMINI_API_KEY in `main.py` with your actual API key:



### 3. Run the FastAPI Backend

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

### 4. Run the Streamlit Frontend

```bash
streamlit run app.py
```

The web app will be available at `http://localhost:8501`

## Usage Guide 📖

### Step 1: Enter Product URL
- Paste any product URL from supported stores (Amazon, eBay, Walmart, etc.)
- Click "Analyze Product" to extract information

### Step 2: Ask AI Questions
- Use natural language to ask about the product
- Examples:
  - "Is this good for travel?"
  - "Summarize all the reviews"
  - "What are the pros and cons?"
  - "Is this good value for money?"

### Step 3: Compare Across Stores
- Click "Compare with Other Stores"
- Get AI-powered comparison analysis
- View similar products with links to other platforms

## API Endpoints 🔌

### POST /scrape-product
Extract product information from any URL
```json
{
  "url": "https://www.amazon.com/product-link"
}
```

### POST /ask-question
Ask AI questions about a product
```json
{
  "product_data": {...},
  "question": "Is this good for travel?"
}
```

### POST /compare-products
Compare with similar products from other stores
```json
{
  "product_data": {...}
}
```

## Supported Websites 🌐

- **Amazon** (amazon.com, amazon.co.uk, etc.)
- **eBay** (ebay.com)
- **Walmart** (walmart.com)
- **Generic stores** (Most e-commerce websites)

The system uses intelligent scraping to adapt to different website structures.



## Configuration ⚙️

### Environment Variables
Create a `.env` file:
```
GEMINI_API_KEY=your_api_key_here
BACKEND_URL=http://localhost:8000
```

### Custom Headers
The system uses realistic browser headers to avoid blocking:
- User-Agent rotation
- Accept headers
- Connection settings

## Troubleshooting 🔧

### Common Issues

1. **"Connection error"**
   - Make sure FastAPI backend is running on port 8000
   - Check if the URL in `app.py` matches your backend URL

2. **"Error scraping product"**
   - Some websites may block requests
   - Try different products or websites
   - Check if the URL is accessible

3. **"Gemini API error"**
   - Verify your API key is correct
   - Check your API quota/billing
   - Ensure you have access to Gemini Pro

4. **Empty product data**
   - Website structure might be different
   - The scraper will attempt generic extraction
   - Try products from supported major retailers




## Limitations & Known Issues ⚠️

1. **Website Blocking**: Some sites may block automated requests
2. **Structure Changes**: Websites frequently change their HTML structure
3. **Rate Limits**: Aggressive scraping may trigger rate limits
4. **Legal Compliance**: Ensure compliance with website terms of service
5. **API Costs**: Gemini API usage incurs costs based on usage

## Future Enhancements 🔮

- [ ] **Image Analysis**: Product image comparison using Vision AI
- [ ] **Price History**: Track price changes over time
- [ ] **User Accounts**: Save favorite products and searches
- [ ] **Mobile App**: React Native or Flutter mobile version
- [ ] **Browser Extension**: Quick product analysis from any page
- [ ] **Email Alerts**: Price drop notifications
- [ ] **Advanced Filtering**: Filter by price range, ratings, etc.
- [ ] **Multi-language**: Support for international stores

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request
