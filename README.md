# PatentNerd: An AI tool to Help Inventors Write Stronger Patents
### Yuge Duan, Abigail Beckler, Dennis Shasha
Patents aim to achieve three objectives: (i) the patent must demonstrate a new idea that lies beyond the state of the art, (ii)  the body of the patent should describe the invented system clearly enough that  one \say{skilled in the art} can realize it, and (iii) the claims should cover variations of what is described in the body that could be realized by the person skilled in the art given what that person has learned in the body.  
  
Whether a patent has achieved these three objectives is often tested in the courts where a patent is used by a plaintiff to make a claim on a commercial product.  The issues in these cases center around three issues (i) whether the patent is in fact novel enough, (ii) whether the patent body clearly supports the claims, (iii) whether the claims, properly understood, constitute an essential part of the commercial product.  Great effort and expense are devoted to all three issues. PatentNerd leverages advanced Large Language Models (LLMs) to help with issue (ii) and partly with issue (iii). The reason we focus on that issue is that (i) is already handled by other excellent tools like like PQAI, PatSnap, IPRally, Amplified, and InnovationQ Plus. Regarding point (iii), future commercial products are impossible to predict, but PatentNerd contributes by suggesting new terms that might be more general but are still supported by the body.  To evaluate PatentNerd's effectiveness, we study lawsuits to determine which portion of the  the court's decisions would have been resolved by PatentNerd.



### Installation Instructions

1. Clone the repository:
   - git clone https://github.com/abeckler21/patentnerd.git
   - cd patentnerd
2. Create and Activate a Virtual Environment
   - python -m venv venv
   - On Windows: venv\Scripts\activate
   - On macOS/Linux: source venv/bin/activate
3. Install dependencies
   - pip install -r requirements.txt

### Usage
1. Start the back-end API:
   - python Code/app.py (or python3 -m Code.app)
2.  Open the front-end UI in a browser