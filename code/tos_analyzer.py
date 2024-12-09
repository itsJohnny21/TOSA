import requests
from bs4 import BeautifulSoup
import re
import json
import os

def fetch_html(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    
def fetch_common_words():
    html_content = fetch_html("http://sherwoodschool.ru/en/vocabulary/proficiency/")
    soup = BeautifulSoup(markup=html_content, features='html.parser')
    
    links = soup.find_all('a', attrs={'target': '_blank'})
    return [link.get_text(strip=True).lower() for link in links if link.text != '']

def parse_html(html_content):
    soup = BeautifulSoup(markup=html_content, features='html.parser')
    for br in soup.find_all('br'):
        br.replace_with(' ')
    
    paragraphs = soup.find_all(['div', 'p', "ol", "ul"])
    return [paragraph.get_text(strip=False) for paragraph in paragraphs]

def analyze_html(html_content, word_ranks):
    paragraphs = parse_html(html_content)
    total_sentences = 0
    total_words = 0
    total_characters = 0
    word_scores = []
    
    for paragraph in paragraphs:
        sentences = []
        
        for sentence in re.split(r'[.?!]+', paragraph):
            sentence = sentence.replace("\n", " ").split(" ")
            sentence = ' '.join(w for w in sentence if w.strip() != '')
            if sentence != '':
                sentences.append(sentence)
                
        total_sentences += len(sentences)
        
        for sentence in sentences:
            words = []
            
            for word in re.split(r'[,\s]+', sentence):
                word = word.replace("\n", " ").split(" ")
                word = ' '.join(w for w in word if w.strip() != '')
                if word != '' and word.isalpha():
                    words.append(word)
                
            total_words += len(words)
            total_characters += sum(len(word) for word in words)
            
            for word in words:
                word = word.lower()
                
                if word not in word_ranks:
                    score = 0
                else:
                    score = 1 - (word_ranks[word] / len(word_ranks))
                    
                word_scores.append(score)
                
    common_word_index = sum(word_scores) / len(word_scores) if word_scores else 0
    
    avg_words_per_sentence = total_words / total_sentences if total_sentences > 0 else 0
    avg_chars_per_word = total_characters / total_words if total_words > 0 else 0
    
    return {
        "total_words": total_words,
        "total_sentences": total_sentences,
        "total_characters": total_characters,
        "avg_words_per_sentence": avg_words_per_sentence,
        "avg_chars_per_word": avg_chars_per_word,
        "common_word_index": common_word_index
    }
    
if __name__ == "__main__":
    if os.path.exists("code/word_ranks.json"):
        with open("code/word_ranks.json", "r") as file:
            try:
                word_ranks = json.load(file)
            except:
                word_ranks = dict()
            
    if not word_ranks:
        word_ranks = {word: index for index, word in enumerate(fetch_common_words())}
        with open("code/word_ranks.json", "w") as file:
            json.dump(word_ranks, file)
    
    tos_metrics = {
        'YouTube': {
            'link': 'https://www.youtube.com/static?template=terms',
            'metrics': {}
        },
        'Meta': {
            'link': 'https://mbasic.facebook.com/legal/terms/preview/printable/',
            'metrics': {}
        },
        'X': {
            'link': 'https://x.com/en/tos',
            'metrics': {}
        },
        'YouTube Simplified': {
            'link': 'resources/simplified_tos/youtube.html',
            'metrics': {}
        },
    }
    
    for company in tos_metrics:
        tos_link = tos_metrics[company]['link']
        
        if os.path.exists(tos_link):
            with open(tos_link, "r") as file:
                html_content = '\n'.join(file.readlines())
        else:
            html_content = fetch_html(tos_link)
    
        metrics = analyze_html(html_content, word_ranks)
        
        tos_metrics[company]['metrics'] = metrics
        
        print(f"Metrics for {company}:")
        for key, value in metrics.items():
            print(f"{key}: {value}" )
        print()
        
    with open("code/tos_metrics.json", "w") as file:
        json.dump(tos_metrics, file)