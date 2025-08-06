import streamlit as st
import requests
from typing import Dict, Any

st.set_page_config(
    page_title="AI Product Comparison Chatbot",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def initialize_session_state():
    """Initialize session state variables"""
    if 'product_data' not in st.session_state:
        st.session_state.product_data = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'similar_products' not in st.session_state:
        st.session_state.similar_products = []

def scrape_product(url: str) -> Dict[str, Any]:
    """Scrape product information from URL"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/scrape-product",
            json={"url": url},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Connection error: {str(e)}"}

def ask_question(product_data: dict, question: str) -> Dict[str, Any]:
    """Ask AI question about the product"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/ask-question",
            json={"product_data": product_data, "question": question},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Connection error: {str(e)}"}

def compare_products(product_data: dict) -> Dict[str, Any]:
    """Compare products across different platforms"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/compare-products",
            json={"product_data": product_data},
            timeout=45
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Connection error: {str(e)}"}

def display_product_info(product_data: dict):
    """Display product information in a nice format"""
    st.subheader("📦 Product Information")
    
    def detect_region_for_display(url):
        region_names = {
            'EG': '🇪🇬 Egypt',
            'AE': '🇦🇪 UAE', 
            'SA': '🇸🇦 Saudi Arabia',
            'IN': '🇮🇳 India',
            'US': '🇺🇸 United States',
            'UK': '🇬🇧 United Kingdom',
            'DE': '🇩🇪 Germany',
            'FR': '🇫🇷 France'
        }
        
        for domain, region in {
            'amazon.eg': 'EG', 'noon.com': 'AE', 'jumia.com.eg': 'EG',
            'amazon.ae': 'AE', 'amazon.sa': 'SA', 'amazon.in': 'IN',
            'amazon.com': 'US', 'amazon.co.uk': 'UK', 'amazon.de': 'DE'
        }.items():
            if domain in url.lower():
                return region_names.get(region, f'{region} Region')
        return '🌍 Global'
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write(f"**Title:** {product_data.get('title', 'N/A')}")
        st.write(f"**Price:** {product_data.get('price', 'N/A')}")
        st.write(f"**Rating:** {product_data.get('rating', 'N/A')}")
        st.write(f"**Source:** {product_data.get('source', 'N/A')}")
        st.write(f"**Region:** {detect_region_for_display(product_data.get('url', ''))}")
        
        if product_data.get('description'):
            with st.expander("Product Description"):
                st.write(product_data['description'][:500] + "..." if len(product_data['description']) > 500 else product_data['description'])
    
    with col2:
        st.write(f"**URL:** [View Product]({product_data.get('url', '#')})")
        
        if product_data.get('reviews'):
            with st.expander("Sample Reviews"):
                for i, review in enumerate(product_data['reviews'][:3], 1):
                    st.write(f"**Review {i}:** {review[:200]}...")

def display_similar_products(similar_products: list):
    """Display similar products from other platforms"""
    if similar_products:
        st.subheader("🔍 Similar Products from Regional Stores")
        
        for product in similar_products:
            with st.expander(f"{product['platform']}: {product['title'][:60]}..."):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Title:** {product['title']}")
                    st.write(f"**Price:** {product['price']}")
                    st.write(f"**Platform:** {product['platform']}")
                with col2:
                    if product.get('url'):
                        st.markdown(f"[View Product]({product['url']})")
                    else:
                        st.write("Link not available")

def main():
    """Main Streamlit application"""
    initialize_session_state()
    
    st.title("🛍️ AI Product Comparison Chatbot")
    st.markdown("Compare products across multiple online stores and ask AI-powered questions!")
    
    with st.sidebar:
        st.header("Product Input")
        product_url = st.text_input(
            "Enter Product URL:",
            placeholder="https://www.amazon.com/product-link...",
            help="Paste the URL of any product from Amazon, eBay, Walmart, etc."
        )
        
        if st.button("🔍 Analyze Product", type="primary"):
            if product_url:
                with st.spinner("Scraping product information..."):
                    result = scrape_product(product_url)
                    
                    if result.get("success"):
                        st.session_state.product_data = result["data"]
                        st.success("Product loaded successfully!")
                        st.rerun()
                    else:
                        st.error(f"Error: {result.get('error', 'Unknown error')}")
            else:
                st.warning("Please enter a product URL first!")
        
        if st.session_state.product_data:
            st.markdown("---")
            if st.button("📊 Compare with Other Stores", type="secondary"):
                with st.spinner("Searching similar products..."):
                    comparison_result = compare_products(st.session_state.product_data)
                    
                    if comparison_result.get("success"):
                        st.session_state.similar_products = comparison_result.get("similar_products", [])
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": f"**Product Comparison Analysis:**\n\n{comparison_result.get('comparison', 'No comparison available.')}"
                        })
                        st.success("Comparison completed!")
                        st.rerun()
                    else:
                        st.error(f"Comparison error: {comparison_result.get('error', 'Unknown error')}")
    
    if st.session_state.product_data:
        display_product_info(st.session_state.product_data)
        
        if st.session_state.similar_products:
            display_similar_products(st.session_state.similar_products)
        
        st.markdown("---")
        
        st.subheader("💬 Ask Questions About This Product")
        
        if st.session_state.chat_history:
            st.markdown("### Chat History")
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.markdown(f"**You:** {message['content']}")
                else:
                    st.markdown(f"**AI Assistant:** {message['content']}")
            st.markdown("---")
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_question = st.text_input(
                "Ask anything about this product:",
                placeholder="e.g., 'Is this good for travel?', 'Summarize the reviews', 'What are the pros and cons?'",
                key="question_input"
            )
        
        with col2:
            ask_button = st.button("Ask AI", type="primary")
        
        st.markdown("**Suggested Questions:**")
        col1, col2, col3, col4 = st.columns(4)
        
        suggested_questions = [
            "Is this product good quality?",
            "Summarize the reviews",
            "What are the pros and cons?",
            "Is this good value for money?"
        ]
        
        if 'selected_question' not in st.session_state:
            st.session_state.selected_question = ""
        
        for i, (col, question) in enumerate(zip([col1, col2, col3, col4], suggested_questions)):
            with col:
                if st.button(question, key=f"suggest_{i}"):
                    st.session_state.selected_question = question
                    st.rerun()
        
        if st.session_state.selected_question and not user_question:
            user_question = st.session_state.selected_question
            st.session_state.selected_question = "" 
        
        if ask_button and user_question:
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_question
            })
            
            with st.spinner("AI is thinking..."):
                result = ask_question(st.session_state.product_data, user_question)
                
                if result.get("success"):
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": result["answer"]
                    })
                    st.rerun()
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")
    
    else:
        st.markdown("""
        ## Welcome to the AI Product Comparison Chatbot! 🚀
        
        ### How to use:
        1. **📝 Paste a product URL** from any online store (Amazon, eBay, Walmart, etc.) in the sidebar
        2. **🔍 Click 'Analyze Product'** to extract product information
        3. **📊 Compare with other stores** to find similar products and prices
        4. **💬 Ask AI questions** about the product (quality, reviews, recommendations, etc.)
        
        ### Supported Stores:
        - Amazon
        - eBay  
        - Walmart
        - And many other online retailers!
        
        ### Example Questions You Can Ask:
        - "Is this product good for travel?"
        - "Summarize all the reviews and give me your thoughts"
        - "What are the main pros and cons?"
        - "Is this a good value for the price?"
        - "How does this compare to similar products?"
        
        **Get started by entering a product URL in the sidebar!** 👈
        """)

if __name__ == "__main__":
    main()