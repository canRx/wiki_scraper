import scrapy
import json
import os
from urllib.parse import urlparse

class WikipediaSpider(scrapy.Spider):
    name = "wikipedia_spider"
    allowed_domains = ["de.wikipedia.org"]
    start_urls = [
        'https://de.wikipedia.org/wiki/Silvio_Berlusconi',
        'https://de.wikipedia.org/wiki/Abraham_Lincoln'
    ]

    def parse(self, response):
        title = response.css('span.mw-page-title-main::text').get()
        if not title:
            title = response.css('h1#firstHeading::text').get()
        if not title:
            title = response.xpath('//h1/text()').get()
            
        if not title:
            self.log(f'⚠️ Konnte keinen Titel finden für: {response.url}')
            title = "Unbekannter Titel"
        else:
            title = title.strip()

        paragraphs = response.css('#mw-content-text .mw-parser-output > p').getall()
        content = '\n\n'.join(paragraphs)
        
        sections = []
        current_section = {"title": "Einleitung", "content": []}
        
        for element in response.css('#mw-content-text .mw-parser-output > *'):
            if element.root.tag in ['h2', 'h3', 'h4', 'h5', 'h6']:
                if current_section["content"]:
                    sections.append(current_section)
                
                section_title = ''.join(element.css('::text').getall()).strip()
                current_section = {"title": section_title, "content": []}
            
            elif element.root.tag == 'p':
                paragraph_text = element.get()
                if paragraph_text.strip():
                    current_section["content"].append(paragraph_text)
        
        if current_section["content"]:
            sections.append(current_section)

        data = {
            'url': response.url,
            'title': title,
            'summary': ' '.join([p for p in response.css('#mw-content-text .mw-parser-output > p:first-of-type ::text').getall()]).strip(),
            'full_content': content,
            'sections': sections
        }

        os.makedirs("output", exist_ok=True)

        path = urlparse(response.url).path
        page_name = path.split('/')[-1]
        filename = f"output/{page_name}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.log(f'✅ Datei gespeichert: {filename}')
        return data