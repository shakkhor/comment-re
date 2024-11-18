import pandas as pd
import numpy as np
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
import re
import os

def process_comments(file_path):
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='cp1252')
    
    # Remove rows with empty comments
    df = df.dropna(subset=['Comment'])
    
    def clean_text(text):
        if isinstance(text, str):
            # Only remove punctuation and extra spaces, keep Bengali and English characters
            text = re.sub(r'[^\w\s\u0980-\u09FF]', ' ', text)
            return ' '.join(text.split())
        return ''
    
    df['cleaned_comment'] = df['Comment'].apply(clean_text)
    df = df[df['cleaned_comment'] != '']
    
    return df

def generate_word_frequencies(comments):
    # Combine all comments into one text
    all_text = ' '.join(comments)
    
    # Split into words (considering both English and Bengali)
    words = re.findall(r'\b[\w\u0980-\u09FF]+\b', all_text)
    
    # Calculate word frequencies
    word_freq = Counter(words)
    
    return dict(word_freq)

def create_wordcloud(word_freq, font_path):
    # Create WordCloud with Bengali font
    wordcloud = WordCloud(
        font_path=font_path,
        width=1600,
        height=800,
        background_color='white',
        prefer_horizontal=0.7,
        min_font_size=10,
        max_font_size=150,
        random_state=42,
        collocations=False  # Disable collocations to improve word rendering
    ).generate_from_frequencies(word_freq)
    
    # Create figure and save
    plt.figure(figsize=(20, 10))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    
    # Save high-resolution image
    output_path = 'wordcloud4.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Word cloud saved as {output_path}")
    
    # Also save word frequencies to a CSV
    freq_df = pd.DataFrame(list(word_freq.items()), columns=['Word', 'Frequency'])
    freq_df = freq_df.sort_values('Frequency', ascending=False)
    freq_df.to_csv('word_frequencies.csv', index=False, encoding='utf-8')
    print("Word frequencies saved to word_frequencies.csv")

def main():
    # Define the absolute path to your Bengali font (make sure the font supports ligatures)
    font_path = 'NotoSansBengali-Regular.ttf'  # Replace with the actual path to the font file
    
    if not os.path.exists(font_path):
        print(f"Font file not found at {font_path}. Please provide the correct path.")
        return
    
    # Use the font for word cloud generation
    print(f"Using font: {font_path}")
    
    try:
        # Process comments
        df = process_comments('output.csv')
        
        if len(df) == 0:
            print("No valid comments found in the CSV file")
            return
        
        print(f"Processing {len(df)} comments...")
        
        # Generate word frequencies
        word_freq = generate_word_frequencies(df['cleaned_comment'])
        
        # Create and save word cloud
        create_wordcloud(word_freq, font_path)
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
