"""
Add Keyword Script
=================

Simple script to add keywords to keywords.txt file.
"""

from keyword_file_manager import add_keyword_to_file, get_current_keywords

def add_keyword():
    """Interactive script to add keywords"""
    
    print("🔍 Current keywords:")
    current_keywords = get_current_keywords()
    for i, keyword in enumerate(current_keywords, 1):
        print(f"   {i}. {keyword}")
    
    print(f"\n📋 Total keywords: {len(current_keywords)}")
    print("\n" + "="*50)
    
    while True:
        print("\n➕ Add new keyword (or 'quit' to exit):")
        new_keyword = input("Enter keyword: ").strip()
        
        if new_keyword.lower() == 'quit':
            print("👋 Goodbye!")
            break
        
        if not new_keyword:
            print("❌ Please enter a keyword")
            continue
        
        success = add_keyword_to_file(new_keyword)
        if success:
            print(f"✅ Added keyword: '{new_keyword}'")
            print("\n📋 Updated keywords:")
            updated_keywords = get_current_keywords()
            for i, keyword in enumerate(updated_keywords, 1):
                print(f"   {i}. {keyword}")
        else:
            print(f"❌ Failed to add keyword: '{new_keyword}'")

if __name__ == "__main__":
    add_keyword() 