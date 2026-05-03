import re

# NLP engine - uses fast, reliable regex extraction
# FLAN-T5 text-generation is not suited for entity extraction so we use rules
print("NLP Engine: Using high-accuracy regex extraction pipeline.")

def extract_income(text: str) -> int:
    if not text:
        return 0
    text_lower = text.lower()
    print(f"DEBUG NLP: Extracting income from: '{text}'")

    # Look for patterns like "25 lakhs", "25 lakh", "1200000", "12 lac", "12L"
    lakh_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lakh|lac|l\b)', text_lower)
    if lakh_match:
        val = float(lakh_match.group(1))
        income = int(val * 100000)
        print(f"DEBUG NLP: Found lakh income: {income}")
        return income

    # crore pattern
    crore_match = re.search(r'(\d+(?:\.\d+)?)\s*crore', text_lower)
    if crore_match:
        val = float(crore_match.group(1))
        income = int(val * 10000000)
        print(f"DEBUG NLP: Found crore income: {income}")
        return income

    # Plain number (likely annual salary in rupees if > 10000)
    nums = re.findall(r'\b(\d{4,})\b', text.replace(',', ''))
    if nums:
        income = int(nums[0])
        print(f"DEBUG NLP: Found raw number income: {income}")
        return income

    print("DEBUG NLP: No income found.")
    return 0

def extract_loan_amount(text: str) -> int:
    if not text: return 0
    text_lower = text.lower()
    
    # Check if words indicating loan/borrowing exist
    if any(w in text_lower for w in ["loan", "need", "borrow", "want", "lakh", "lac", "crore", "amount"]):
        lakh_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lakh|lac|l\b)', text_lower)
        if lakh_match: return int(float(lakh_match.group(1)) * 100000)
        crore_match = re.search(r'(\d+(?:\.\d+)?)\s*crore', text_lower)
        if crore_match: return int(float(crore_match.group(1)) * 10000000)
        nums = re.findall(r'\b(\d{4,})\b', text.replace(',', ''))
        if nums: return int(nums[0])
    return 0


PROFESSION_KEYWORDS = [
    "software engineer", "engineer", "developer", "programmer", "architect",
    "doctor", "physician", "surgeon", "nurse", "dentist",
    "teacher", "professor", "lecturer", "educator",
    "lawyer", "advocate", "attorney", "chartered accountant", "ca",
    "accountant", "auditor", "finance",
    "manager", "analyst", "consultant", "advisor",
    "designer", "artist", "photographer",
    "business", "entrepreneur", "self-employed", "contractor",
    "pilot", "officer", "government",
    "student", "intern",
]

def extract_profession(text: str) -> str:
    if not text:
        return ""
    text_lower = text.lower()
    print(f"DEBUG NLP: Extracting profession from: '{text}'")

    for kw in PROFESSION_KEYWORDS:
        if kw in text_lower:
            # Capitalize nicely
            profession = kw.title()
            print(f"DEBUG NLP: Found profession: {profession}")
            return profession

    # Fallback: look for "I am a/an X" or "I work as X"
    match = re.search(r'(?:i am a[n]?|i work as a[n]?|profession is|i\'m a[n]?)\s+(\w+(?:\s+\w+)?)', text_lower)
    if match:
        profession = match.group(1).strip().title()
        print(f"DEBUG NLP: Found profession via phrase: {profession}")
        return profession

    return "Professional"


def analyze_risk(text: str) -> str:
    if not text:
        return "LOW"
    text_lower = text.lower()
    high_risk_words = ["debt", "loan", "emi", "credit card", "overdue", "bankrupt", "unemployed", "no income"]
    for word in high_risk_words:
        if word in text_lower:
            return "HIGH"
    return "LOW"
