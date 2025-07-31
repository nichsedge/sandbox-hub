import requests
import os
import time
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import re

def search_gutenberg_balzac():
    """Search for Balzac works on Project Gutenberg"""
    search_url = "https://www.gutenberg.org/ebooks/search/?query=Honor%C3%A9+de+Balzac&submit_search=Go%21"
    
    try:
        response = requests.get(search_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        books = []
        # Find book links
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if '/ebooks/' in href and href.count('/') == 2:
                book_id = href.split('/')[-1]
                if book_id.isdigit():
                    title = link.get_text(strip=True)
                    if title and 'Balzac' in response.text:
                        books.append((book_id, title))
        
        return books[:10]  # Limit to first 10 books
    except Exception as e:
        print(f"Error searching: {e}")
        return []

def download_book(book_id, title):
    """Download book from Project Gutenberg"""
    txt_url = f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt"
    
    try:
        response = requests.get(txt_url)
        if response.status_code == 200:
            # Clean filename
            safe_title = re.sub(r'[^\w\s-]', '', title)[:50]
            filename = f"{book_id}_{safe_title}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"Downloaded: {filename}")
            return filename
        else:
            print(f"Failed to download {title}")
            return None
    except Exception as e:
        print(f"Error downloading {title}: {e}")
        return None

def translate_text_chunks(text, chunk_size=4000):
    """Translate text in chunks to avoid API limits"""
    translator = GoogleTranslator(source='en', target='id')
    
    # Split text into chunks
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    translated_chunks = []
    
    for i, chunk in enumerate(chunks):
        try:
            translated = translator.translate(chunk)
            translated_chunks.append(translated)
            print(f"Translated chunk {i+1}/{len(chunks)}")
            time.sleep(1)  # Rate limiting
        except Exception as e:
            print(f"Translation error for chunk {i+1}: {e}")
            translated_chunks.append(chunk)  # Keep original if translation fails
    
    return ' '.join(translated_chunks)

def translate_book(filename):
    """Translate downloaded book to Indonesian"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove Gutenberg header/footer
        start_marker = "*** START OF"
        end_marker = "*** END OF"
        
        start_idx = content.find(start_marker)
        if start_idx != -1:
            start_idx = content.find('\n', start_idx) + 1
        else:
            start_idx = 0
            
        end_idx = content.find(end_marker)
        if end_idx == -1:
            end_idx = len(content)
        
        book_text = content[start_idx:end_idx].strip()
        
        if len(book_text) > 100:  # Only translate if substantial content
            print(f"Translating {filename}...")
            translated_text = translate_text_chunks(book_text)
            
            # Save translated version
            translated_filename = filename.replace('.txt', '_indonesian.txt')
            with open(translated_filename, 'w', encoding='utf-8') as f:
                f.write(translated_text)
            
            print(f"Translated: {translated_filename}")
        else:
            print(f"Skipping {filename} - insufficient content")
            
    except Exception as e:
        print(f"Error translating {filename}: {e}")

def main():
    """Main function to download and translate Balzac works"""
    print("Searching for Balzac works...")
    books = search_gutenberg_balzac()
    
    if not books:
        print("No books found. Using manual list...")
        # Manual list of known Balzac works
        books = [
            ("1968", "The Magic Skin"),
            ("1438", "The Wild Ass's Skin"),
            ("1307", "Father Goriot"),
            ("1709", "Eugenie Grandet")
        ]
    
    print(f"Found {len(books)} books")
    
    # Create output directory
    os.makedirs("balzac_books", exist_ok=True)
    os.chdir("balzac_books")
    
    for book_id, title in books:
        print(f"\nProcessing: {title}")
        filename = download_book(book_id, title)
        
        if filename:
            translate_book(filename)
        
        time.sleep(2)  # Be respectful to servers

if __name__ == "__main__":
    # Install required packages
    try:
        import deep_translator
        import bs4
    except ImportError:
        print("Installing required packages...")
        os.system("pip install deep-translator beautifulsoup4 requests")
    
    main()