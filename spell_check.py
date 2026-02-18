import re

def check_spelling():
    with open('templates/certificate_template.svg', 'r') as f:
        content = f.read()
        
    # Find all <text>...</text> content
    texts = re.findall(r'<text[^>]*>(.*?)</text>', content)
    
    words = set()
    print("--- Text Content ---")
    for t in texts:
        print(f"Line: {t}")
        # Strip XML tags if nested (though unlikely for simple text)
        clean_text = re.sub(r'<[^>]+>', '', t)
        # Split
        clean_words = re.sub(r'[^\w\s]', '', clean_text)
        for w in clean_words.split():
            words.add(w)
            
    print("\n--- Unique Words ---")
    for w in sorted(list(words)):
        print(w)

if __name__ == "__main__":
    check_spelling()
