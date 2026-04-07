"""
Link Detection Module
Advanced link detection for Telegram messages with support for:
- URL entities
- Text links
- Regex pattern matching
- Telegram link filtering
- Domain extraction and validation
"""

import re
from typing import List, Tuple, Optional
from telegram import MessageEntity


class LinkDetector:
    """Advanced link detection for Telegram messages"""
    
    # Comprehensive URL pattern
    URL_PATTERN = re.compile(
        r'(https?://[^\s<>"{}|\\^`\[\]]+)'  # http/https URLs
        r'|(www\.[^\s<>"{}|\\^`\[\]]+)'      # www. URLs
        r'|(t\.me/[^\s<>"{}|\\^`\[\]]+)'     # Telegram links
        r'|(tg://[^\s<>"{}|\\^`\[\]]+)',     # tg:// protocol links
        re.IGNORECASE
    )
    
    # Telegram official domains (allowed when blocking external links)
    TELEGRAM_DOMAINS = [
        't.me/',
        'telegram.me/',
        'telegram.dog/',
        'tg://',
        'te.legra.ph/',
        'graph.org/',
        'telegra.ph/'
    ]
    
    # Common URL shorteners (often used for spam)
    URL_SHORTENERS = [
        'bit.ly/', 'tinyurl.com/', 'short.link/', 'is.gd/',
        't.co/', 'ow.ly/', 'buff.ly/', 'cutt.ly/',
        'shorte.st/', 'linkvertise.com/', 'rb.gy/'
    ]
    
    @classmethod
    def detect_links(cls, text: str, entities: Optional[List[MessageEntity]] = None) -> Tuple[bool, List[str]]:
        """
        Detect links in message text and entities
        
        Args:
            text: Message text or caption
            entities: List of message entities
            
        Returns:
            Tuple of (has_links, list_of_urls)
        """
        urls_found = []
        
        # Check entities first (most reliable)
        if entities:
            entity_urls = cls._extract_urls_from_entities(text, entities)
            urls_found.extend(entity_urls)
        
        # Fallback to regex pattern matching
        if not urls_found and text:
            regex_urls = cls._extract_urls_from_regex(text)
            urls_found.extend(regex_urls)
        
        has_links = len(urls_found) > 0
        return has_links, urls_found
    
    @classmethod
    def _extract_urls_from_entities(cls, text: str, entities: List[MessageEntity]) -> List[str]:
        """Extract URLs from Telegram message entities"""
        urls = []
        
        for entity in entities:
            if entity.type == 'url':
                # Extract URL from text based on entity position
                url = text[entity.offset:entity.offset + entity.length]
                if url:
                    urls.append(url)
            
            elif entity.type == 'text_link' and entity.url:
                # Hidden link (text with URL)
                urls.append(entity.url)
            
            elif entity.type == 'custom_emoji' and hasattr(entity, 'url') and entity.url:
                # Custom emoji with link (rare)
                urls.append(entity.url)
        
        return urls
    
    @classmethod
    def _extract_urls_from_regex(cls, text: str) -> List[str]:
        """Extract URLs using regex pattern matching"""
        urls = []
        matches = cls.URL_PATTERN.findall(text)
        
        # findall returns tuples for groups, flatten them
        for match in matches:
            # match is a tuple of groups, get the non-empty one
            url = next((m for m in match if m), None)
            if url:
                # Clean up trailing punctuation
                url = cls._clean_url(url)
                urls.append(url)
        
        return urls
    
    @classmethod
    def _clean_url(cls, url: str) -> str:
        """Clean URL by removing trailing punctuation"""
        # Remove trailing punctuation that's not part of URL
        while url and url[-1] in '.,;:!?)]}\'"':
            url = url[:-1]
        return url
    
    @classmethod
    def is_telegram_link(cls, url: str) -> bool:
        """Check if URL is a Telegram official link"""
        url_lower = url.lower()
        return any(domain in url_lower for domain in cls.TELEGRAM_DOMAINS)
    
    @classmethod
    def is_url_shortener(cls, url: str) -> bool:
        """Check if URL is a known URL shortener"""
        url_lower = url.lower()
        return any(shortener in url_lower for shortener in cls.URL_SHORTENERS)
    
    @classmethod
    def extract_domain(cls, url: str) -> Optional[str]:
        """Extract domain from URL"""
        try:
            # Remove protocol
            if '://' in url:
                url = url.split('://')[1]
            
            # Get domain
            domain = url.split('/')[0]
            return domain.lower()
        except:
            return None
    
    @classmethod
    def detect_external_links(cls, text: str, entities: Optional[List[MessageEntity]] = None) -> Tuple[bool, List[str]]:
        """
        Detect external (non-Telegram) links
        
        Args:
            text: Message text or caption
            entities: List of message entities
            
        Returns:
            Tuple of (has_external_links, list_of_external_urls)
        """
        has_links, all_urls = cls.detect_links(text, entities)
        
        if not has_links:
            return False, []
        
        # Filter out Telegram links
        external_urls = [url for url in all_urls if not cls.is_telegram_link(url)]
        
        return len(external_urls) > 0, external_urls
    
    @classmethod
    def get_link_type(cls, url: str) -> str:
        """
        Classify link type
        
        Returns:
            Link type: 'telegram', 'shortener', 'external', 'unknown'
        """
        if cls.is_telegram_link(url):
            return 'telegram'
        elif cls.is_url_shortener(url):
            return 'shortener'
        elif cls.extract_domain(url):
            return 'external'
        else:
            return 'unknown'
    
    @classmethod
    def detect_links_with_info(cls, text: str, entities: Optional[List[MessageEntity]] = None) -> dict:
        """
        Detect links and return detailed information
        
        Returns:
            Dictionary with link detection results
        """
        has_links, urls = cls.detect_links(text, entities)
        
        if not has_links:
            return {
                'has_links': False,
                'total_links': 0,
                'urls': [],
                'telegram_links': [],
                'external_links': [],
                'shorteners': [],
                'link_types': []
            }
        
        # Classify links
        telegram_links = [url for url in urls if cls.is_telegram_link(url)]
        external_links = [url for url in urls if not cls.is_telegram_link(url)]
        shorteners = [url for url in urls if cls.is_url_shortener(url)]
        
        link_types = [cls.get_link_type(url) for url in urls]
        
        return {
            'has_links': True,
            'total_links': len(urls),
            'urls': urls,
            'telegram_links': telegram_links,
            'external_links': external_links,
            'shorteners': shorteners,
            'link_types': link_types
        }
