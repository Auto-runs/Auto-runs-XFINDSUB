# XFINDSUB

**XFINDSUB** is a passive subdomain enumeration tool with a clean and interactive CLI interface (powered by `rich` + `pyfiglet`).  
It gathers subdomains from multiple public sources and optionally validates them with DNS resolution.  

---

## ✨ Features
- 🔎 Passive subdomain enumeration from:
  - [crt.sh](https://crt.sh)
  - [AlienVault OTX](https://otx.alienvault.com/)
  - [Bufferover](https://dns.bufferover.run/)
- ✅ Optional DNS resolution (check if subdomains are alive)  
- 📂 Output to **stdout**, **TXT**, or **JSON**  
- 🎨 Fancy CLI interface (banner + spinner progress)  
- ⚡ Supports single domain or multiple domains (via list file)  

---

## 📦 Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/username/xfindsub.git
cd xfindsub
pip install -r requirements.txt

## 🚀 Usage 

```bash
# Single domain
python xfindsub.py -d example.com

# List of domains
python xfindsub.py -l domains.txt

# With DNS resolution
python xfindsub.py -d example.com --resolve

# Output results (TXT)
python xfindsub.py -d example.com -o result.txt

# Output results (JSON)
python xfindsub.py -d example.com --json result.json

# Silent mode (only print subdomains)
python xfindsub.py -d example.com --silent

# Custom sources
python xfindsub.py -d example.com --sources crtsh,otx

📂 Project Structure
xfindsub/
│── xfindsub.py        # main program
│── resolver.py        # async DNS resolver
│── sources/
│   ├── crtsh.py
│   ├── otx.py
│   ├── bufferover.py
│── requirements.txt
└── README.md

📝 Disclaimer

This project is intended for educational purposes, penetration testing, bug bounty, and research only.
Do not use it for illegal activities.